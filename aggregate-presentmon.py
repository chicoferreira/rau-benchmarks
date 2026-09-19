import csv
import math
import statistics
import sys
from pathlib import Path

METRICS = ("FrameTime", "CPUBusy", "GPUTime")

if len(sys.argv) < 3:
    sys.exit(f"usage: {Path(__file__).name} <input.csv|-> <output.csv> [label=value ...]")

input_path, output_path, *labels = sys.argv[1:]
values_by_metric = {metric: [] for metric in METRICS}
header = []

if input_path == "-":
    source = open(sys.stdin.fileno(), encoding="utf-8-sig", newline="", closefd=False)
else:
    source = Path(input_path).open(encoding="utf-8-sig", newline="")

with source as file:

    def data_lines(file):
        for line in file:
            if len(header) < 2:
                header.append(line.rstrip("\r\n"))
            yield line

    for row in csv.DictReader(data_lines(file)):
        for metric, values in values_by_metric.items():
            values.append(float(row[metric]))

if not values_by_metric[METRICS[0]]:
    sys.exit(f"error: no frames were captured from {input_path}")


def percentile(values, percentage):
    position = (len(values) - 1) * percentage
    lower = math.floor(position)
    upper = math.ceil(position)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


rows = []

for metric, values in values_by_metric.items():
    values.sort()
    rows.append(
        {
            "metric": metric,
            "count": len(values),
            "total_ms": round(sum(values), 6),
            "average_ms": round(statistics.fmean(values), 6),
            "stddev_ms": round(statistics.pstdev(values), 6),
            "min_ms": round(values[0], 6),
            "p50_ms": round(percentile(values, 0.50), 6),
            "p90_ms": round(percentile(values, 0.90), 6),
            "p95_ms": round(percentile(values, 0.95), 6),
            "p99_ms": round(percentile(values, 0.99), 6),
            "max_ms": round(values[-1], 6),
        }
    )

comments = [label.replace("=", ": ", 1) for label in labels] + header
output_path = Path(output_path)

with output_path.open("w", encoding="utf-8", newline="") as file:
    for comment in comments:
        file.write(f"# {comment}\r\n")
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(output_path)
