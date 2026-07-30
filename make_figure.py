"""
Generate the headline two-panel figure from predictions.csv.

Panel A: grouped bar chart of %Personal and %Emotional across three groups
         (Reddit all 4 subs / Reddit advice 3 subs / WildChat).
Panel B: stacked bar chart of P×E cell composition (0/0, 1/0, 0/1, 1/1)
         by source, as percentages so cell mix is comparable.

Run: python3 make_figure.py
Writes: figures/headline.png
"""

import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

PREDICTIONS_CSV = "predictions.csv"
ADVICE_SUBS = {"relationship_advice", "socialskills", "personalfinance"}
OUTPUT = "figures/headline.png"

# Apply the spot-check correction documented in results.md (rd_a3wjd 0/1 -> 0/0,
# rd_a1im9 1/0 -> 1/1) so the figure matches the human-corrected matrix.
CORRECTIONS = {
    "rd_a3wjd": (0, 0),
    "rd_a1im9": (1, 1),
}

PERSONAL_COLOR = "#2E5EAA"
EMOTIONAL_COLOR = "#E07B39"

CELL_COLORS = {
    "0/0": "#D9D9D9",   # neither — light grey
    "1/0": "#2E5EAA",   # personal, not emotional — blue (the dominant Reddit pattern)
    "0/1": "#999999",   # emotional, not personal — mid grey (empty in this corpus)
    "1/1": "#E07B39",   # both — orange
}


def load() -> list[dict]:
    rows = []
    with open(PREDICTIONS_CSV) as f:
        for r in csv.DictReader(f):
            p, e = int(r["personal"]), int(r["emotional"])
            if r["id"] in CORRECTIONS:
                p, e = CORRECTIONS[r["id"]]
            r["personal"], r["emotional"] = p, e
            rows.append(r)
    return rows


def pct(rows: list[dict], attr: str) -> float:
    return sum(r[attr] for r in rows) / len(rows) * 100


def cell_pcts(rows: list[dict]) -> dict[str, float]:
    counts = Counter((r["personal"], r["emotional"]) for r in rows)
    n = len(rows)
    return {f"{p}/{e}": counts.get((p, e), 0) / n * 100 for p in (0, 1) for e in (0, 1)}


def cell_counts(rows: list[dict]) -> dict[str, int]:
    counts = Counter((r["personal"], r["emotional"]) for r in rows)
    return {f"{p}/{e}": counts.get((p, e), 0) for p in (0, 1) for e in (0, 1)}


def main():
    rows = load()
    reddit = [r for r in rows if r["source"] == "reddit"]
    advice = [r for r in reddit if r["subreddit"] in ADVICE_SUBS]
    wildchat = [r for r in rows if r["source"] == "wildchat"]

    groups = [
        ("Reddit\n(all 4 subs)", reddit),
        ("Reddit advice\n(3 subs)", advice),
        ("WildChat\n(first turns)", wildchat),
    ]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5.5), gridspec_kw={"width_ratios": [1.15, 1]})

    # === Panel A: grouped bar of %P and %E ===
    labels = [g[0] for g in groups]
    p_vals = [pct(g[1], "personal") for g in groups]
    e_vals = [pct(g[1], "emotional") for g in groups]
    x = list(range(len(labels)))
    width = 0.38

    bars_p = ax_a.bar([i - width / 2 for i in x], p_vals, width, label="% Personal",
                      color=PERSONAL_COLOR, edgecolor="white", linewidth=0.5)
    bars_e = ax_a.bar([i + width / 2 for i in x], e_vals, width, label="% Emotional",
                      color=EMOTIONAL_COLOR, edgecolor="white", linewidth=0.5)

    for bars, vals in [(bars_p, p_vals), (bars_e, e_vals)]:
        for bar, v in zip(bars, vals):
            ax_a.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                      f"{v:.1f}%", ha="center", va="bottom", fontsize=10, color="#222")

    ax_a.set_xticks(x)
    ax_a.set_xticklabels(labels, fontsize=10)
    ax_a.set_ylabel("Percentage of messages", fontsize=11)
    ax_a.set_ylim(0, 105)
    ax_a.set_title("A. Personal and emotional content by source",
                   fontsize=12, fontweight="bold", loc="left", pad=12)
    ax_a.legend(loc="upper right", frameon=False, fontsize=10)
    ax_a.spines["top"].set_visible(False)
    ax_a.spines["right"].set_visible(False)
    ax_a.set_axisbelow(True)
    ax_a.yaxis.grid(True, linestyle=":", alpha=0.5)

    # Annotate the gap. Computed from the unrounded rates rather than written in
    # by hand — dividing the rounded display values (91 / 0.7) inflates this to
    # "130-fold", which is the wrong number and cannot drift back in if it is
    # derived here.
    fold_gap = p_vals[1] / p_vals[2]  # Reddit advice %P over WildChat %P
    ax_a.annotate("", xy=(2 - width / 2, 5), xytext=(1 - width / 2, 88),
                  arrowprops=dict(arrowstyle="-|>", color="#777", lw=1.2,
                                  connectionstyle="arc3,rad=-0.25"))
    ax_a.text(1.5, 55, f"~{fold_gap:.0f}-fold gap\non Personal", fontsize=9, color="#444",
              ha="center", style="italic")

    # === Panel B: stacked bar of P×E composition ===
    sources = [("Reddit\n(N=1,500)", reddit), ("WildChat\n(N=1,493)", wildchat)]
    cell_order = ["0/0", "1/0", "0/1", "1/1"]
    cell_labels = {
        "0/0": "Neither",
        "1/0": "Personal,\nnot emotional",
        "0/1": "Emotional,\nnot personal",
        "1/1": "Both",
    }

    bottoms = [0.0, 0.0]
    bar_x = [0, 1]
    bar_width = 0.55
    for cell in cell_order:
        heights = [cell_pcts(g[1])[cell] for g in sources]
        counts = [cell_counts(g[1])[cell] for g in sources]
        ax_b.bar(bar_x, heights, bar_width, bottom=bottoms,
                 color=CELL_COLORS[cell], edgecolor="white", linewidth=1.2,
                 label=f"{cell}  {cell_labels[cell]}")
        for i, (h, c, b) in enumerate(zip(heights, counts, bottoms)):
            if h >= 3:  # only label segments large enough to read
                ax_b.text(bar_x[i], b + h / 2, f"{c}\n({h:.1f}%)",
                          ha="center", va="center", fontsize=9,
                          color="white" if cell in ("1/0", "1/1") else "#222")
        bottoms = [b + h for b, h in zip(bottoms, heights)]

    ax_b.set_xticks(bar_x)
    ax_b.set_xticklabels([s[0] for s in sources], fontsize=10)
    ax_b.set_ylabel("Share of messages (%)", fontsize=11)
    ax_b.set_ylim(0, 100)
    ax_b.set_title("B. P × E cell composition (human-corrected)",
                   fontsize=12, fontweight="bold", loc="left", pad=12)
    ax_b.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False,
                fontsize=9, title="Cell (P/E)", title_fontsize=10, alignment="left")
    ax_b.spines["top"].set_visible(False)
    ax_b.spines["right"].set_visible(False)

    fig.suptitle(
        "What people type to a chatbot vs. to a Reddit advice forum",
        fontsize=14, fontweight="bold", y=0.995,
    )
    fig.text(
        0.5, 0.02,
        "Sources: WildChat-1M (2023–2024) · Reddit advice subs (2009–2013).  "
        "Classifier: Claude Sonnet 4.6.  N = 2,993.  Codebook: coding_scheme.md",
        ha="center", fontsize=8.5, color="#555", style="italic",
    )

    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    Path("figures").mkdir(exist_ok=True)
    plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
