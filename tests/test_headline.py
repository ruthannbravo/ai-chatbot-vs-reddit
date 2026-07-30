"""
Assert that every number published in README.md, results.md, and
research_article.md still follows from the committed predictions.csv.

This exists because the four-cell matrix in the README once drifted out of sync
with the data (it summed to 1,499 instead of 1,500) and nothing caught it. Any
future edit that changes the labels, or any writeup edit that changes a quoted
figure without changing the data, now fails CI.

Run: python3 tests/test_headline.py
"""

import csv
import sys
from collections import Counter
from pathlib import Path

from scipy.stats import chi2_contingency

REPO = Path(__file__).resolve().parent.parent
ADVICE_SUBS = {"relationship_advice", "socialskills", "personalfinance"}

# The two manual flips from the spot check, as documented in results.md. Kept in
# sync with make_figure.py by the test at the bottom.
CORRECTIONS = {"rd_a3wjd": (0, 0), "rd_a1im9": (1, 1)}

failures = []


def check(label: str, actual, expected) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected}, got {actual}")


def pct1(rows: list[dict], attr: str) -> float:
    """Percentage rounded to 1dp — the precision the writeups quote."""
    return round(sum(r[attr] for r in rows) / len(rows) * 100, 1)


def matrix(rows: list[dict]) -> tuple[int, int, int, int]:
    c = Counter((r["personal"], r["emotional"]) for r in rows)
    return c[(0, 0)], c[(1, 0)], c[(0, 1)], c[(1, 1)]


def load(apply_corrections: bool) -> list[dict]:
    rows = []
    with open(REPO / "predictions.csv") as f:
        for r in csv.DictReader(f):
            p, e = int(r["personal"]), int(r["emotional"])
            if apply_corrections and r["id"] in CORRECTIONS:
                p, e = CORRECTIONS[r["id"]]
            r["personal"], r["emotional"] = p, e
            rows.append(r)
    return rows


def main() -> int:
    raw = load(apply_corrections=False)
    corrected = load(apply_corrections=True)

    reddit = [r for r in raw if r["source"] == "reddit"]
    wildchat = [r for r in raw if r["source"] == "wildchat"]
    advice = [r for r in reddit if r["subreddit"] in ADVICE_SUBS]

    # --- Sample sizes (README badge, results.md:4, data_notes.md) ---
    check("total N", len(raw), 2993)
    check("Reddit N", len(reddit), 1500)
    check("WildChat N", len(wildchat), 1493)
    check("Reddit advice N", len(advice), 1125)
    check("duplicate ids", len(raw) - len({r["id"] for r in raw}), 0)

    # --- Headline table (README, results.md, research_article.md §4.1) ---
    check("Reddit all-4 %P", pct1(reddit, "personal"), 71.3)
    check("Reddit all-4 %E", pct1(reddit, "emotional"), 31.8)
    check("Reddit advice %P", pct1(advice, "personal"), 90.8)
    check("Reddit advice %E", pct1(advice, "emotional"), 41.3)
    check("WildChat %P", pct1(wildchat, "personal"), 0.7)
    check("WildChat %E", pct1(wildchat, "emotional"), 0.1)

    # Aggregate rates must be identical with and without the corrections — the
    # two flips are both Reddit Emotional and cancel. results.md asserts this.
    red_corr = [r for r in corrected if r["source"] == "reddit"]
    check("corrections leave %P unchanged", pct1(red_corr, "personal"), pct1(reddit, "personal"))
    check("corrections leave %E unchanged", pct1(red_corr, "emotional"), pct1(reddit, "emotional"))

    # --- Per-subreddit table (results.md, research_article.md §4.2) ---
    for sub, exp_p, exp_e in [
        ("relationship_advice", 93.6, 64.5),
        ("socialskills", 90.7, 47.2),
        ("personalfinance", 88.0, 12.3),
        ("LifeProTips", 13.1, 3.2),
    ]:
        group = [r for r in reddit if r["subreddit"] == sub]
        check(f"{sub} N", len(group), 375)
        check(f"{sub} %P", pct1(group, "personal"), exp_p)
        check(f"{sub} %E", pct1(group, "emotional"), exp_e)

    # --- P x E matrices, both rows (results.md, README, article §4.3) ---
    check("Reddit raw matrix", matrix(reddit), (429, 594, 1, 476))
    check("Reddit corrected matrix", matrix(red_corr), (430, 593, 0, 477))
    check("WildChat matrix", matrix(wildchat), (1482, 10, 0, 1))
    # Every published matrix row must account for all N. This is the specific
    # regression that motivated this file.
    check("Reddit raw matrix sums to N", sum(matrix(reddit)), 1500)
    check("Reddit corrected matrix sums to N", sum(matrix(red_corr)), 1500)
    check("WildChat matrix sums to N", sum(matrix(wildchat)), 1493)

    # --- Chi-square (results.md, article §4.4) ---
    for label, group_a, attr, exp_chi2 in [
        ("all-4 Personal", reddit, "personal", 1613.20),
        ("all-4 Emotional", reddit, "emotional", 559.09),
        ("advice Personal", advice, "personal", 2173.27),
        ("advice Emotional", advice, "emotional", 743.88),
    ]:
        a_yes = sum(r[attr] for r in group_a)
        b_yes = sum(r[attr] for r in wildchat)
        stat, p, _, _ = chi2_contingency(
            [[a_yes, len(group_a) - a_yes], [b_yes, len(wildchat) - b_yes]]
        )
        check(f"chi2 {label}", round(stat, 2), exp_chi2)
        if p >= 1e-120:
            failures.append(f"chi2 {label}: p={p:.2e} is larger than the reported magnitude")

    # --- The headline fold-gap must be ~123, not the rounded-then-divided 130 ---
    fold = (sum(r["personal"] for r in advice) / len(advice)) / (
        sum(r["personal"] for r in wildchat) / len(wildchat)
    )
    check("Personal fold-gap (1dp)", round(fold, 1), 123.2)

    # --- WildChat positive counts quoted in prose ---
    check("WildChat Personal count", sum(r["personal"] for r in wildchat), 11)
    check("WildChat Emotional count", sum(r["emotional"] for r in wildchat), 1)

    # --- make_figure.py must apply exactly the corrections documented above ---
    fig_src = (REPO / "make_figure.py").read_text()
    for rid in CORRECTIONS:
        if rid not in fig_src:
            failures.append(f"make_figure.py no longer applies the {rid} correction")

    if failures:
        print(f"FAILED — {len(failures)} published number(s) no longer match the data:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("OK — all published headline numbers reproduce from predictions.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
