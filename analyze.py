"""
Analyze predictions.csv: produce the headline table, P×E matrix, per-subreddit
breakdown, and chi-square tests for the Reddit-vs-WildChat distribution
difference. Mirrors the format of pilot_results.md so results are directly
comparable to the 40-row pilot.

Run: python3 analyze.py
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path

from scipy.stats import chi2_contingency

PREDICTIONS_CSV = "predictions.csv"
ADVICE_SUBS = {"relationship_advice", "socialskills", "personalfinance"}


def load_predictions() -> list[dict]:
    rows = []
    with open(PREDICTIONS_CSV) as f:
        for row in csv.DictReader(f):
            row["personal"] = int(row["personal"])
            row["emotional"] = int(row["emotional"])
            rows.append(row)
    return rows


def stats(rows: list[dict]) -> tuple[int, int, int]:
    n = len(rows)
    p = sum(r["personal"] for r in rows)
    e = sum(r["emotional"] for r in rows)
    return n, p, e


def pe_matrix(rows: list[dict]) -> dict[str, int]:
    counts = Counter((r["personal"], r["emotional"]) for r in rows)
    return {
        "0/0": counts.get((0, 0), 0),
        "1/0": counts.get((1, 0), 0),
        "0/1": counts.get((0, 1), 0),
        "1/1": counts.get((1, 1), 0),
    }


def chi2(group_a: list[dict], group_b: list[dict], attr: str) -> tuple[float, float, int, int, int]:
    a_yes = sum(r[attr] for r in group_a)
    a_no = len(group_a) - a_yes
    b_yes = sum(r[attr] for r in group_b)
    b_no = len(group_b) - b_yes
    table = [[a_yes, a_no], [b_yes, b_no]]
    chi2_stat, p, df, _ = chi2_contingency(table)
    return chi2_stat, p, df, a_yes, b_yes


def sig_marker(p: float) -> str:
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"


def main():
    if not Path(PREDICTIONS_CSV).exists():
        raise SystemExit(f"{PREDICTIONS_CSV} not found. Run classify_batch.py first.")

    rows = load_predictions()
    reddit = [r for r in rows if r["source"] == "reddit"]
    wildchat = [r for r in rows if r["source"] == "wildchat"]
    advice = [r for r in reddit if r["subreddit"] in ADVICE_SUBS]

    print(f"\n=== Headline (n={len(rows)}) ===")
    print(f"{'':25} {'N':>5}  {'%P':>6}  {'%E':>6}")
    for label, group in [
        ("Reddit (all 4 subs)", reddit),
        ("Reddit advice (3 subs)", advice),
        ("WildChat", wildchat),
    ]:
        n, p, e = stats(group)
        print(f"{label:25} {n:>5}  {p/n*100:>5.1f}%  {e/n*100:>5.1f}%")

    print(f"\n=== Reddit broken down by subreddit ===")
    print(f"{'Subreddit':25} {'N':>5}  {'P=1':>5}  {'E=1':>5}  {'%P':>6}  {'%E':>6}")
    by_sub = defaultdict(list)
    for r in reddit:
        by_sub[r["subreddit"]].append(r)
    for sub in sorted(by_sub):
        group = by_sub[sub]
        n, p, e = stats(group)
        print(f"{sub:25} {n:>5}  {p:>5}  {e:>5}  {p/n*100:>5.1f}%  {e/n*100:>5.1f}%")

    print(f"\n=== P × E combination matrix ===")
    print(f"{'':10} {'0/0':>6}  {'1/0':>6}  {'0/1':>6}  {'1/1':>6}")
    for label, group in [("Reddit", reddit), ("WildChat", wildchat)]:
        m = pe_matrix(group)
        print(f"{label:10} {m['0/0']:>6}  {m['1/0']:>6}  {m['0/1']:>6}  {m['1/1']:>6}")

    print(f"\n=== Chi-square: Reddit vs WildChat ===")
    print(f"H0: P (or E) is independent of source.")
    for attr_label, attr in [("Personal", "personal"), ("Emotional", "emotional")]:
        chi2_stat, p, df, r_yes, w_yes = chi2(reddit, wildchat, attr)
        print(
            f"  {attr_label:9}  chi2={chi2_stat:8.2f}  df={df}  p={p:.2e}  {sig_marker(p)}  "
            f"(Reddit {r_yes/len(reddit)*100:.1f}%, WildChat {w_yes/len(wildchat)*100:.1f}%)"
        )
    print("  Sig: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")

    # Also test on the advice-subs-only restriction (matches pilot_results.md)
    print(f"\n=== Chi-square: Reddit advice (3 subs) vs WildChat ===")
    for attr_label, attr in [("Personal", "personal"), ("Emotional", "emotional")]:
        chi2_stat, p, df, r_yes, w_yes = chi2(advice, wildchat, attr)
        print(
            f"  {attr_label:9}  chi2={chi2_stat:8.2f}  df={df}  p={p:.2e}  {sig_marker(p)}  "
            f"(Advice {r_yes/len(advice)*100:.1f}%, WildChat {w_yes/len(wildchat)*100:.1f}%)"
        )


if __name__ == "__main__":
    main()
