import csv
import math
import statistics
import sys
from array import array
from collections import defaultdict
from pathlib import Path


def percentile(values, percentage):
    position = (len(values) - 1) * percentage
    lower = math.floor(position)
    upper = math.ceil(position)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def aggregate(input_path, output_path, launches=1):
    """Summarize a span capture, grouped by scope, by depth and by the data a
    span was given.

    A capture holding several launches end to end is averaged over them, so
    every total is what one launch cost. The per-call columns are unaffected.
    """
    durations_by_span = defaultdict(lambda: array("q"))
    header = []

    with input_path.open(encoding="utf-8", newline="") as file:

        def data_lines(file):
            for line in file:
                if line.startswith("#"):
                    header.append(line.rstrip("\r\n"))
                else:
                    yield line

        for row in csv.DictReader(data_lines(file)):
            # `data` is what the span was given to tell instances apart, such as
            # the resource type a sync step ran for. It is absent from a capture
            # written before that column existed.
            key = (row["scope"], int(row["depth"]), row.get("data", ""))
            durations_by_span[key].append(int(row["duration_ns"]))

    if not durations_by_span:
        sys.exit(f"error: no spans were captured in {input_path}")

    rows = []

    for (scope, depth, data), durations in durations_by_span.items():
        durations = sorted(durations)
        to_ms = lambda value: round(value / 1_000_000, 6)
        rows.append(
            {
                "scope": scope,
                "depth": depth,
                "data": data,
                "count": len(durations),
                "total_ms": to_ms(sum(durations) / launches),
                "average_ms": to_ms(statistics.fmean(durations)),
                "stddev_ms": to_ms(statistics.pstdev(durations)),
                "min_ms": to_ms(durations[0]),
                "p50_ms": to_ms(percentile(durations, 0.50)),
                "p90_ms": to_ms(percentile(durations, 0.90)),
                "p95_ms": to_ms(percentile(durations, 0.95)),
                "p99_ms": to_ms(percentile(durations, 0.99)),
                "max_ms": to_ms(durations[-1]),
            }
        )

    rows.sort(key=lambda row: row["total_ms"], reverse=True)

    if launches > 1:
        header.append(f"# launches: {launches}")

    with output_path.open("w", encoding="utf-8", newline="") as file:
        for line in header:
            file.write(f"{line}\r\n")
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(f"usage: {Path(__file__).name} <input.csv> <output.csv> [launches]")

    input_path, output_path = map(Path, sys.argv[1:3])
    aggregate(input_path, output_path, int(sys.argv[3]) if len(sys.argv) > 3 else 1)
