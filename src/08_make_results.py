"""
08_make_results.py  --  works offline once data/clean/snapshots.csv exists.

WHAT THIS DOES (in plain English)
---------------------------------
Turns the numbers from 06_analyze.py into things you can drop into the paper:

  TABLES (CSV files; open in Google Sheets / Excel, copy into your Google Doc)
    results/table_calibration.csv      price bucket vs actual win rate, per horizon
    results/table_long_favourites.csv  long shots & favourites, with margins
    results/table_cost_test.csv        average profit per share at each trading cost

  FIGURES (PNG images; Insert > Image in Google Docs)
    results/figure_calibration.png     price vs actual win rate (the main figure)
    results/figure_gaps.png            gap with margin of error, long shots & favourites

It uses exactly the same rules as 06_analyze.py. It changes nothing in your data
and invents no new tests, so running it is safe (see the pre-registration).

TRY IT BEFORE YOU HAVE REAL DATA (fake data):
    python3 src/08_make_results.py --fake

HOW TO RUN (needs matplotlib:  python3 -m pip install matplotlib)
    python3 src/08_make_results.py
"""

import csv
import math
import os
import random
import sys
from datetime import datetime

import matplotlib
matplotlib.use("Agg")                  # draw to files, no window needed
import matplotlib.pyplot as plt

SNAPSHOT_FILE = "data/clean/snapshots.csv"
OUT_FOLDER = "results"
NUM_BUCKETS = 10
HORIZONS = ["7d", "1d", "1h"]
CATEGORIES = ["politics", "sports"]
MIN_PER_GROUP = 30
COSTS_CENTS = [0, 1, 2, 4]
THRESHOLDS = {"primary": (0.30, 0.70), "strict": (0.10, 0.90)}
COMPARISON_START = datetime.fromisoformat("2025-10-01T00:00:00+00:00").timestamp()

# One colour per category (blue = politics, orange = sports). Same colour every figure.
COLORS = {"politics": "#2a78d6", "sports": "#eb6834"}
INK = "#0b0b0b"          # text
GREY = "#52514e"         # secondary text
LIGHT_GREY = "#c9c8c3"   # grid and reference lines


# ----------------------------------------------------------------------------
# LOADING DATA  (same as 06_analyze.py)
# ----------------------------------------------------------------------------
def load_rows():
    rows = []
    with open(SNAPSHOT_FILE) as f:
        for r in csv.DictReader(f):
            rows.append({
                "event_id": r["event_id"], "category": r["category"],
                "horizon": r["horizon"], "price": float(r["price"]),
                "won": int(r["won"]), "closed_time": float(r["closed_time"]),
            })
    return rows


def fake_rows():
    random.seed(1)
    rows = []
    for k in range(3000):
        true_prob = random.random()
        price = min(0.97, max(0.03, 0.5 + (true_prob - 0.5) * 0.8))
        rows.append({
            "event_id": str(k // 3), "category": random.choice(CATEGORIES),
            "horizon": random.choice(HORIZONS), "price": price,
            "won": 1 if random.random() < true_prob else 0,
            "closed_time": random.choice([1.7e9, 1.77e9]),
        })
    return rows


# ----------------------------------------------------------------------------
# HELPER FUNCTIONS  (same maths as 06_analyze.py)
# ----------------------------------------------------------------------------
def mean(values):
    return sum(values) / len(values)


def mean_and_error(values, clusters):
    """Average of 'values' plus a 95% margin of error. Markets from the same
    event are added together first, because they are not independent."""
    n = len(values)
    avg = mean(values)
    totals = {}
    for v, c in zip(values, clusters):
        totals[c] = totals.get(c, 0.0) + (v - avg)
    se = math.sqrt(sum(t * t for t in totals.values())) / n
    return avg, 1.96 * se


def gap_and_margin(group):
    """Gap (actual - price) and its 95% margin for a list of snapshots."""
    return mean_and_error([r["won"] - r["price"] for r in group],
                          [r["event_id"] for r in group])


def write_csv(filename, header, table_rows):
    path = os.path.join(OUT_FOLDER, filename)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(table_rows)
    print("wrote", path)


def bucket_label(i):
    return f"{i / NUM_BUCKETS:.0%}-{(i + 1) / NUM_BUCKETS:.0%}"


def split_buckets(rows):
    buckets = [[] for _ in range(NUM_BUCKETS)]
    for r in rows:
        buckets[min(int(r["price"] * NUM_BUCKETS), NUM_BUCKETS - 1)].append(r)
    return buckets


# ----------------------------------------------------------------------------
# TABLE 1: calibration by price bucket
# ----------------------------------------------------------------------------
def make_calibration_table(rows):
    out = []
    for horizon in HORIZONS:
        subset = [r for r in rows if r["horizon"] == horizon]
        for i, g in enumerate(split_buckets(subset)):
            if not g:
                continue
            avg_p = mean([r["price"] for r in g])
            actual = mean([r["won"] for r in g])
            _, margin = gap_and_margin(g)
            note = "fewer than 30" if len(g) < MIN_PER_GROUP else ""
            out.append([horizon, bucket_label(i), len(g), round(avg_p, 3),
                        round(actual, 3), round(actual - avg_p, 3), round(margin, 3), note])
        brier = mean([(r["price"] - r["won"]) ** 2 for r in subset])
        out.append([horizon, "Brier score", len(subset), "", "", "", "", round(brier, 4)])
    write_csv("table_calibration.csv",
              ["horizon", "price bucket", "n", "average price", "actual win rate",
               "gap", "margin (95%)", "note"], out)


# ----------------------------------------------------------------------------
# TABLE 2: long shots and favourites
# ----------------------------------------------------------------------------
def make_long_favourite_table(rows):
    recent = [r for r in rows if r["closed_time"] >= COMPARISON_START]
    out = []
    for sample_name, sample in (("full period", rows), ("comparison year", recent)):
        for category in CATEGORIES:
            cat_rows = [r for r in sample if r["category"] == category]
            for horizon in HORIZONS:
                subset = [r for r in cat_rows if r["horizon"] == horizon]
                for label, (low, high) in THRESHOLDS.items():
                    for group_name, group in (
                        (f"long shots <{low:.2f}", [r for r in subset if r["price"] < low]),
                        (f"favourites >{high:.2f}", [r for r in subset if r["price"] > high]),
                    ):
                        if not group:
                            out.append([sample_name, category, horizon, group_name, 0, "", "", "", "", ""])
                            continue
                        gap, margin = gap_and_margin(group)
                        avg_p = mean([r["price"] for r in group])
                        actual = mean([r["won"] for r in group])
                        if len(group) < MIN_PER_GROUP:
                            verdict = "too few to test"
                        elif abs(gap) < margin:
                            verdict = "within margin (could be luck)"
                        else:
                            verdict = "larger than margin"
                        out.append([sample_name, category, horizon, group_name, len(group),
                                    round(avg_p, 3), round(actual, 3), round(gap, 3),
                                    round(margin, 3), verdict])
    write_csv("table_long_favourites.csv",
              ["sample", "category", "horizon", "group", "n", "average price",
               "actual win rate", "gap", "margin (95%)", "verdict"], out)


# ----------------------------------------------------------------------------
# TABLE 3: cost test
# ----------------------------------------------------------------------------
def make_cost_table(rows):
    out = []
    for category in CATEGORIES:
        cat_rows = [r for r in rows if r["category"] == category]
        for horizon in HORIZONS:
            subset = [r for r in cat_rows if r["horizon"] == horizon]
            for name, group, sign in (
                ("bet against long shots (<0.30)", [r for r in subset if r["price"] < 0.30], +1),
                ("back favourites (>0.70)", [r for r in subset if r["price"] > 0.70], -1),
            ):
                if len(group) < MIN_PER_GROUP:
                    out.append([category, horizon, name, len(group), "too few to test", "", "", ""])
                    continue
                cells = []
                for cost in COSTS_CENTS:
                    profits = [100 * sign * (r["price"] - r["won"]) - cost for r in group]
                    avg, margin = mean_and_error(profits, [r["event_id"] for r in group])
                    cells.append(f"{avg:+.1f} (+/-{margin:.1f})")
                out.append([category, horizon, name, len(group)] + cells)
    write_csv("table_cost_test.csv",
              ["category", "horizon", "bet", "n"] + [f"{c}c cost: cents per share (+/- 95% margin)" for c in COSTS_CENTS],
              out)


# ----------------------------------------------------------------------------
# FIGURE 1: calibration plot
# ----------------------------------------------------------------------------
def style_axes(ax):
    """Plain, quiet look: no top/right border, light grid."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(LIGHT_GREY)
    ax.tick_params(colors=GREY, labelsize=9)
    ax.grid(True, color=LIGHT_GREY, linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)


def make_calibration_figure(rows):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.9), sharex=True, sharey=True)
    for ax, horizon in zip(axes, HORIZONS):
        style_axes(ax)
        ax.plot([0, 1], [0, 1], color=GREY, linewidth=1, linestyle="--")   # perfect calibration
        for category in CATEGORIES:
            subset = [r for r in rows if r["category"] == category and r["horizon"] == horizon]
            xs, ys, errs, small = [], [], [], []
            for g in split_buckets(subset):
                if not g:
                    continue
                avg_p = mean([r["price"] for r in g])
                actual, margin = mean_and_error([r["won"] for r in g], [r["event_id"] for r in g])
                xs.append(avg_p); ys.append(actual); errs.append(margin)
                small.append(len(g) < MIN_PER_GROUP)
            ax.errorbar(xs, ys, yerr=errs, color=COLORS[category], linewidth=1.4,
                        marker="o", markersize=5, capsize=2, label=category)
            # groups with fewer than 30 snapshots are drawn hollow
            for x, y, is_small in zip(xs, ys, small):
                if is_small:
                    ax.plot(x, y, marker="o", markersize=5, markerfacecolor="white",
                            markeredgecolor=COLORS[category], linestyle="none", zorder=5)
        ax.set_title(f"{horizon} before decided", color=INK, fontsize=11, loc="left")
        ax.set_xlim(0, 1); ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel("average price", color=GREY, fontsize=9)
    axes[0].set_ylabel("share that actually won", color=GREY, fontsize=9)
    axes[0].legend(frameon=False, fontsize=9, loc="upper left")
    fig.text(0.01, -0.02,
             "Dashed line = perfect calibration. Bars = 95% margin of error. "
             "Hollow points = fewer than 30 snapshots.",
             color=GREY, fontsize=8)
    fig.tight_layout()
    path = os.path.join(OUT_FOLDER, "figure_calibration.png")
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


# ----------------------------------------------------------------------------
# FIGURE 2: gaps with margins (primary thresholds only)
# ----------------------------------------------------------------------------
def make_gap_figure(rows):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    low, high = THRESHOLDS["primary"]
    for ax, (title, test) in zip(axes, ((f"Long shots (price < {low:.2f})", lambda p: p < low),
                                        (f"Favourites (price > {high:.2f})", lambda p: p > high))):
        style_axes(ax)
        ax.axhline(0, color=GREY, linewidth=1)
        for offset, category in zip((-0.08, 0.08), CATEGORIES):
            for i, horizon in enumerate(HORIZONS):
                group = [r for r in rows if r["category"] == category
                         and r["horizon"] == horizon and test(r["price"])]
                if len(group) < MIN_PER_GROUP:
                    ax.text(i + offset, 0.005, "too few", color=GREY, fontsize=7,
                            rotation=90, ha="center", va="bottom")
                    continue
                gap, margin = gap_and_margin(group)
                ax.errorbar(i + offset, gap, yerr=margin, color=COLORS[category],
                            marker="o", markersize=6, capsize=3, linewidth=1.4,
                            label=category if i == 0 else None)
        ax.set_xticks(range(len(HORIZONS)))
        ax.set_xticklabels(HORIZONS)
        ax.set_xlim(-0.5, len(HORIZONS) - 0.5)
        ax.set_title(title, color=INK, fontsize=11, loc="left")
        ax.set_xlabel("time before decided", color=GREY, fontsize=9)
    axes[0].set_ylabel("gap = actual win rate - price", color=GREY, fontsize=9)
    axes[0].legend(frameon=False, fontsize=9, loc="best")
    fig.text(0.01, -0.02,
             "Bars = 95% margin of error. A gap whose bar crosses zero cannot be told apart from luck.",
             color=GREY, fontsize=8)
    fig.tight_layout()
    path = os.path.join(OUT_FOLDER, "figure_gaps.png")
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
os.makedirs(OUT_FOLDER, exist_ok=True)
rows = fake_rows() if "--fake" in sys.argv else load_rows()
make_calibration_table(rows)
make_long_favourite_table(rows)
make_cost_table(rows)
make_calibration_figure(rows)
make_gap_figure(rows)
print("\nDone. Open the CSV files in Google Sheets and copy the tables into your paper.")
