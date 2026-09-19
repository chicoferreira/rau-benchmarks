"""Compare the frame times of two runs of one tool.

    python compare.py ssao/rau/results/<run-name> ssao/rau/results/<other-run-name>

Each folder holds the summary `aggregate-presentmon.py` wrote for that run,
or several when a run was repeated, each counted as one sample.
"""

import csv
import statistics
import sys
from pathlib import Path

METRICS = ("FrameTime", "CPUBusy", "GPUTime")


def run_means(directory):
    paths = sorted(directory.glob("*-ssao.csv"))
    if not paths:
        sys.exit(f"No summaries in {directory}")

    means = {metric: [] for metric in METRICS}
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as file:
            lines = (line for line in file if not line.startswith("#"))
            summary = {row["metric"]: row for row in csv.DictReader(lines)}
        for metric in METRICS:
            means[metric].append(float(summary[metric]["average_ms"]))

    return means


baseline_dir, candidate_dir = map(Path, sys.argv[1:3])
baseline = run_means(baseline_dir)
candidate = run_means(candidate_dir)

print(f"{baseline_dir.name} (n={len(baseline['FrameTime'])})", end=" -> ")
print(f"{candidate_dir.name} (n={len(candidate['FrameTime'])})")
print()

for metric in METRICS:
    before, after = baseline[metric], candidate[metric]
    mean_before, mean_after = statistics.fmean(before), statistics.fmean(after)

    print(
        f"{metric:<10}"
        f"{mean_before:.4f} +-{statistics.pstdev(before):.4f}"
        f" -> {mean_after:.4f} +-{statistics.pstdev(after):.4f} ms"
        f"  {(mean_after - mean_before) / mean_before:+7.1%}"
    )
