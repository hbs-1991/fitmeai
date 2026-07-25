"""Render a dated series to a PNG. Reads JSON on stdin, prints the output path.

Deliberately knows nothing about FatSecret: no API client, no config, no
environment. It is reachable from the agent's Bash, and everything reachable from
Bash is assumed readable by the agent — so it is given nothing worth reading.

    echo '[{"date":"2026-07-20","value":82.4}]' \\
      | fatsecret-chart --out /tmp/w.png --title Weight --ylabel kg
"""

from __future__ import annotations

import argparse
import json
import sys

import matplotlib
matplotlib.use("Agg")          # no display in a container; must precede pyplot
import matplotlib.pyplot as plt  # noqa: E402


def render(series: list[dict], out_path: str, title: str = "", ylabel: str = "") -> str:
    if not series:
        raise ValueError("series is empty; nothing to plot")
    try:
        labels = [str(p["date"]) for p in series]
        values = [float(p["value"]) for p in series]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"each point needs a 'date' and a numeric 'value': {exc}") from exc

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(labels, values, marker="o", linewidth=2)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    # Dense date labels overlap into mush past ~10 points; thin them, keep the last.
    step = max(1, len(labels) // 10)
    ax.set_xticks(range(0, len(labels), step))
    ax.set_xticklabels(labels[::step], rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Render a dated JSON series to a PNG.")
    ap.add_argument("--out", required=True, help="output PNG path")
    ap.add_argument("--title", default="")
    ap.add_argument("--ylabel", default="")
    args = ap.parse_args()
    try:
        series = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"stdin is not valid JSON: {exc}", file=sys.stderr)
        return 2
    try:
        print(render(series, args.out, args.title, args.ylabel))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
