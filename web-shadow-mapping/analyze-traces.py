#!/usr/bin/env python3
"""Per-frame CPU cost of the browser traces in ./results.

Usage:  python analyze-traces.py [results/*.json.gz ...]
"""

import bisect
import glob
import gzip
import json
import os
import statistics as st
from collections import Counter
import sys

WARMUP_S = 5


def percentile(xs, p):
    xs = sorted(xs)
    k = (len(xs) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def parse(path):
    raf, gputask = [], []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s.startswith("{"):
                continue
            if s.endswith(","):
                s = s[:-1]
            try:
                e = json.loads(s)
            except ValueError:
                continue
            ph, name = e.get("ph"), e.get("name", "")
            if ph == "X" and name == "FireAnimationFrame":
                raf.append((e["ts"], e.get("dur", 0), e["pid"]))
            elif ph == "X" and name == "GPUTask":
                rpid = e.get("args", {}).get("data", {}).get("renderer_pid")
                gputask.append((e["ts"], e.get("dur", 0), rpid))
    return raf, gputask


def merge(spans):
    """Total time covered by a set of (start, end) intervals, overlap once."""
    spans = sorted(spans)
    total, cur_s, cur_e = 0, spans[0][0], spans[0][1]
    for s, e in spans[1:]:
        if s > cur_e:
            total += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    return total + cur_e - cur_s


def cost(path):
    """(avg, p95, frames) of the per-frame cost, in milliseconds."""
    raf, gputask = parse(path)
    raf.sort()
    # the page under test is whichever process drew the most frames
    renderer = Counter(pid for _, _, pid in raf).most_common(1)[0][0]
    raf = [r for r in raf if r[2] == renderer]
    raf = [r for r in raf if r[0] >= raf[0][0] + WARMUP_S * 1_000_000]
    starts = [r[0] for r in raf]

    spans = [[(ts, ts + dur)] for ts, dur, _ in raf]
    for ts, dur, rpid in gputask:
        if rpid != renderer or ts < starts[0]:
            continue
        i = bisect.bisect_right(starts, ts) - 1
        if 0 <= i < len(raf):
            spans[i].append((ts, ts + dur))

    per_frame = [merge(s) / 1000.0 for s in spans]
    return st.mean(per_frame), percentile(per_frame, 95), len(per_frame)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(here, "results", "*.json.gz")))
    print("%-28s %8s %8s %8s" % ("", "avg", "p95", "frames"))
    for p in paths:
        avg, p95, n = cost(p)
        print("%-28s %8.3f %8.3f %8d" % (os.path.basename(p), avg, p95, n))


if __name__ == "__main__":
    main()
