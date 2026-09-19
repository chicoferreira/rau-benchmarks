# Shadow Mapping Copies

The shadow mapping example copied 10, 100 and 1000 times into one project, with only one copy drawn, to see how Rau's frame, load and save times grow with the number of resources. The web versions of the load and save times are in `../web-load-save/`.

## Generating the projects

The projects are not kept in this repository. They take their shaders from the shadow mapping example of the [Rau repository](https://github.com/chicoferreira/rau), here at `../rau`. From this repository's root, recreate them with:

```sh
rau generate shadow-mapping-10-copies copies/shadow-mapping-10
cp ../rau/projects/shadow-mapping/*.wgsl copies/shadow-mapping-10/

rau generate shadow-mapping-100-copies copies/shadow-mapping-100
cp ../rau/projects/shadow-mapping/*.wgsl copies/shadow-mapping-100/

rau generate shadow-mapping-1000-copies copies/shadow-mapping-1000
cp ../rau/projects/shadow-mapping/*.wgsl copies/shadow-mapping-1000/
```

## Frame cost

```sh
./copies/bench-internal.sh <run-name> 10
./copies/bench-internal.sh <run-name> 100
./copies/bench-internal.sh <run-name> 1000
```

Each run opens the project in the regular editor at 1920x1080 with v-sync off, in Rau's benchmark mode (`--benchmark`), which writes one row per profiler span. Ten seconds are discarded and 30 are recorded, then `aggregate_spans.py` averages each span into `copies/results/<run-name>/shadow-mapping-<copies>-internal.csv`. `KEEP_RAW=1` also keeps the raw capture, which can be summarised again with:

```sh
python copies/aggregate_spans.py <raw.csv> <summary.csv>
```

## Loading and saving

```sh
python copies/bench-load-save.py <run-name>            # 10 launches, 10, 100 and 1000 copies
python copies/bench-load-save.py <run-name> 20 100     # 20 launches of one
```

Each launch opens the project in benchmark mode, which also records the load (`--benchmark-load`). The load is timed from the lines Rau prints on its way up. Once the load is recorded, Control+S is pressed in the window and the save is read from the spans of the two seconds after it. The first launch is a warm-up and is not measured.

Written to `copies/results/<run-name>/`:

- `load.csv`, the average of the launches, in milliseconds:
  - `startup_ms`, from starting Rau until it printed its renderer backend, with the window open and the device set up;
  - `open_ms`, then until it printed that the project is open;
  - `build_ms`, then until benchmark mode recorded the load, with nothing left to build;
  - `ready_ms` and `total_ms`, the last two together and all three together;
  - `save_ms`, the `ProjectSaveState::save` span;
  - `serialize_ms`, the `Project::serialize` span inside it;
  - `write_ms`, the `write file` span, which runs on a separate thread, outside the frame.
- `shadow-mapping-<copies>-loading.csv`, every span of the load averaged over the launches, such as the time spent building each kind of resource.
