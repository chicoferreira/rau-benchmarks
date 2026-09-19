# Rau benchmarks

The benchmarks behind the performance analysis of the dissertation on [Rau](https://github.com/chicoferreira/rau).

- `ssao/` draws the same SSAO scene in Rau, in Nau3D, in SHADERed, and in a baseline program written directly against WGPU, and compares their CPU time, GPU time and memory. `ssao/nau3d/README.md` and `ssao/shadered/README.md` list how those two versions of the scene differ from Rau's.
- `copies/` measures how Rau's frame, load and save times grow as a project holds 10, 100 and 1000 copies of the shadow mapping example.
- `web-shadow-mapping/` compares Rau and SHADERed in the browser on the shadow mapping scene.

## Requirements

The desktop benchmarks run on Windows, from a Bash shell such as Git Bash, with Python 3 and these on the `PATH`:

- `rau-bin`, built from the Rau repository in the `dist` profile;
- `PresentMon-2.5.1-x64`, [PresentMon](https://github.com/GameTechDev/PresentMon) 2.5.1;
- `composerImGui`, from the [Nau3D](https://github.com/Nau3D/nau) release;
- `SHADERed.exe`, [SHADERed](https://github.com/dfranx/SHADERed) 1.5.6.

The baseline program is built with Cargo from `ssao/baseline/`.

## Results

Recorded on an AMD Ryzen 7 7700X with 32 GB of DDR5-6000 and an AMD Radeon RX 9070 XT, Windows 11 Pro 25H2 (build 26200.9168), driver 32.0.31041.1004. Rau is commit `c678b14`, DX12 backend, `dist` profile.

### SSAO on the desktop

| Tool                          | CPU avg | CPU p95 | GPU avg | GPU p95 | Working set | Private bytes |
| ----------------------------- | ------- | ------- | ------- | ------- | ----------- | ------------- |
| Written directly against WGPU | 0.159 ms | 0.172 ms | 0.325 ms | 0.370 ms | 172 MiB | 321 MiB |
| Rau, DX12                     | 0.367 ms | 0.385 ms | 0.406 ms | 0.475 ms | 256 MiB | 438 MiB |
| Rau, DX12, focus view         | 0.242 ms | 0.275 ms | 0.358 ms | 0.423 ms | 260 MiB | 443 MiB |
| Nau3D, OpenGL                 | 0.360 ms | 0.420 ms | 0.390 ms | 0.445 ms | 178 MiB | 537 MiB |
| SHADERed, OpenGL              | 0.374 ms | 0.436 ms | 0.408 ms | 0.456 ms | 221 MiB | 721 MiB |

Times are PresentMon's `CPUBusy` and `GPUTime`. The memory columns are read once after 30 seconds of drawing.

### Shadow mapping in the browser

Per-frame CPU time, from Chrome 152.0.7977.65 traces read by `web-shadow-mapping/analyze-traces.py`.

| Tool             |   avg |   p95 |
| ---------------- | ----- | ----- |
| Rau, WebGPU      | 0.757 ms | 0.912 ms |
| Rau, WebGL2      | 0.916 ms | 1.062 ms |
| SHADERed, WebGL2 | 1.137 ms | 1.234 ms |

### Frame cost as a project grows

Average time of a frame in Rau, with the shadow mapping example copied 10, 100 and 1000 times into one project and only one copy drawn. Each indented row is part of the less indented row above it.

|  | 250 resources | 2,500 resources | 25,000 resources |
| --- | ---: | ---: | ---: |
| Frame | 0.420 ms | 0.582 ms | 2.374 ms |
| &emsp;Interface | 0.104 ms | 0.212 ms | 1.378 ms |
| &emsp;&emsp;Viewport tabs | 0.019 ms | 0.096 ms | 0.930 ms |
| &emsp;&emsp;Resource tree | 0.047 ms | 0.074 ms | 0.363 ms |
| &emsp;&emsp;Status bar | 0.007 ms | 0.008 ms | 0.026 ms |
| &emsp;&emsp;Remaining panels | 0.032 ms | 0.034 ms | 0.058 ms |
| &emsp;Engine | 0.121 ms | 0.177 ms | 0.744 ms |
| &emsp;&emsp;Sync step | 0.003 ms | 0.012 ms | 0.111 ms |
| &emsp;&emsp;Save check | 0.002 ms | 0.017 ms | 0.168 ms |
| &emsp;&emsp;Presentation errors | 0.002 ms | 0.013 ms | 0.131 ms |
| &emsp;&emsp;Submitted revision | 0.002 ms | 0.013 ms | 0.126 ms |
| &emsp;&emsp;Camera update | 0.001 ms | 0.006 ms | 0.063 ms |
| &emsp;&emsp;Pass encoding | 0.077 ms | 0.078 ms | 0.097 ms |
| &emsp;&emsp;Submission to the device | 0.035 ms | 0.036 ms | 0.047 ms |
| &emsp;Painting (`eframe`) | 0.149 ms | 0.149 ms | 0.193 ms |

### Loading and saving as a project grows

The same projects, launched with the project opened and then saved.

|  | 250 resources | 2,500 resources | 25,000 resources |
| --- | ---: | ---: | ---: |
| Launch | 477.4 ms | 581.3 ms | 1,833.5 ms |
| &emsp;Startup | 359.1 ms | 359.9 ms | 358.5 ms |
| &emsp;Load | 118.3 ms | 221.4 ms | 1,474.9 ms |
| &emsp;&emsp;Opening the project | 48.0 ms | 49.4 ms | 65.2 ms |
| &emsp;&emsp;Building the resources | 70.3 ms | 172.1 ms | 1,409.8 ms |
| Save | 0.7 ms | 5.9 ms | 64.9 ms |
| &emsp;Serializing the project | 0.7 ms | 5.9 ms | 64.8 ms |

### Breakdown of building time per resource kind

Largest project only. `Building` is the resources' own build, `Deciding` the rest of the sync step. Viewports are not synced, hence 23,000 of 25,000 resources.

| Resource | Count | Sync step | Building | Deciding |
| --- | ---: | ---: | ---: | ---: |
| Shader | 2,000 | 661.220 ms | 660.765 ms | 0.455 ms |
| Render pipeline | 2,000 | 407.212 ms | 386.499 ms | 20.713 ms |
| Texture view | 4,000 | 90.351 ms | 28.142 ms | 62.209 ms |
| Bind group | 3,000 | 74.452 ms | 4.616 ms | 69.836 ms |
| Uniform | 2,000 | 60.931 ms | 35.248 ms | 25.684 ms |
| Texture | 4,000 | 40.122 ms | 34.838 ms | 5.284 ms |
| Render pass | 2,000 | 12.344 ms | 0.899 ms | 11.445 ms |
| Camera | 2,000 | 2.818 ms | 0.182 ms | 2.636 ms |
| Dimension | 2,000 | 0.203 ms | 0.053 ms | 0.150 ms |
| Model | 0 | 0.003 ms | 0.000 ms | 0.003 ms |
| Sampler | 0 | 0.002 ms | 0.000 ms | 0.002 ms |
| Compute pass | 0 | 0.000 ms | 0.000 ms | 0.000 ms |
| **Total** | **23,000** | **1,349.658 ms** | **1,151.242 ms** | **198.416 ms** |

## Running everything

The shadow mapping copy projects have to be generated first, as described in `copies/README.md`. Then, from the root of this repository:

```sh
./bench-all.sh <run-name>
```

It runs every desktop benchmark in turn, memory and load and save times included, and writes their summaries into a `results/<run-name>/` folder beside each one. How to run a single benchmark is described in `ssao/README.md` and `copies/README.md`. The browser traces are recorded by hand, as described in `web-shadow-mapping/README.md`.

## Licence and credits

The scripts are under the MIT licence (`LICENSE.md`). The backpack model (`ssao/backpack.obj`) is [Survival Guitar Backpack](https://sketchfab.com/3d-models/survival-guitar-backpack-low-poly-799f8c4511f84fab8c3f12887f7e6b36) by Berk Gedik, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), in the version distributed with [LearnOpenGL](https://learnopengl.com/Model-Loading/Model).
