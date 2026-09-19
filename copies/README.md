# Shadow Mapping Copies

From the root of this repository, with the [Rau repository](https://github.com/chicoferreira/rau) checked out next to it, recreate the projects with:

```sh
rau generate shadow-mapping-10-copies copies/shadow-mapping-10
cp ../rau/projects/shadow-mapping/*.wgsl copies/shadow-mapping-10/

rau generate shadow-mapping-100-copies copies/shadow-mapping-100
cp ../rau/projects/shadow-mapping/*.wgsl copies/shadow-mapping-100/

rau generate shadow-mapping-1000-copies copies/shadow-mapping-1000
cp ../rau/projects/shadow-mapping/*.wgsl copies/shadow-mapping-1000/
```

Record where the frame goes with:

```sh
./copies/bench-internal.sh final 10
./copies/bench-internal.sh final 100
./copies/bench-internal.sh final 1000
```

Each run opens the project in the regular editor at 1920x1080 with v-sync off, in Rau's `--benchmark` mode, which writes one row per profiler span. Ten seconds are discarded and 30 are recorded, then `aggregate_spans.py` averages each span into `copies/results/<run-name>/shadow-mapping-<count>-internal.csv`. `KEEP_RAW=1` also keeps the raw capture, which can be summarised again with:

```sh
python copies/aggregate_spans.py copies/results/<run-name>/shadow-mapping-10-internal-raw.csv copies/results/<run-name>/shadow-mapping-10-internal.csv
```

Time how long the projects take to load and to save, and record where a load spends its time, with:

```sh
python copies/bench-load-save.py final            # 10, 100 and 1000
python copies/bench-load-save.py final 20 100     # 20 launches of one
```
