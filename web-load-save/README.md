# Loading and Saving in the Web

The same load and save times as `../copies/bench-load-save.py`, measured in the web build.

## Requirements

Python 3 with [Playwright](https://playwright.dev/python/) (`pip install playwright`), and Google Chrome. The copy projects have to be generated first, as described in `../copies/README.md`, and the web version built in the Rau repository next to this one with `./web/build-web.sh`, with `wasm-opt` on the `PATH` so it is optimised as the deployed one is (the deploy uses [binaryen](https://github.com/WebAssembly/binaryen) `version_132`).

## Running

From the root of this repository:

```sh
python web-load-save/bench.py <run-name>            # 10 launches, 10, 100 and 1000 copies
python web-load-save/bench.py <run-name> 20 100     # 20 launches of one
```

`rau_site.py`, which the browser benchmarks in `../web-shadow-mapping/` also use, serves the build with the same headers as the live site. Every file is cached, so after the first load nothing goes over the network. To test another site, set `RAU_SITE`, for example `RAU_SITE=https://rau.chicoferreira.dev/`.

Chrome runs with a fresh profile, so no extensions or other tabs get in the way. Each copy project is served from `../copies/` as if it were on GitHub and created in IndexedDB once, so GitHub takes no part. Each launch then opens the project from IndexedDB in Rau's benchmark mode, set from the URL as `--benchmark` and `--benchmark-load` are on the desktop. The first launch is a warm-up and is not measured.

The load is timed from the lines the app logs, stamped in the page's own clock. Once the load is recorded, Control+S is pressed and the save is read from the spans of the two seconds after it, which the page downloads as a CSV.

## Output

`results/<run-name>/load.csv`, with the same columns as the desktop:

- `startup_ms`, until the app logged its renderer backend, once the wasm is loaded and the device set up;
- `open_ms`, then until it logged that the project is open;
- `build_ms`, then until benchmark mode recorded the load, with nothing left to build;
- `ready_ms` and `total_ms`, the last two together and all three together;
- `save_ms`, the `ProjectSaveState::save` span;
- `serialize_ms`, the `Project::serialize` span inside it;
- `write_ms`, handing the file to IndexedDB, the `consume task` span of `save file`: copying it out of the WebAssembly memory, and IndexedDB copying it again before it writes it asynchronously. Unlike the desktop, it runs on the page's single thread, in the same frame as the save, right after it. The write to the IndexedDB itself is not included.
