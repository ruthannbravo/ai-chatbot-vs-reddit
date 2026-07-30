"""
Generate a stratified random sample of predictions for manual QA — 52 rows
under the plan below.

Reads predictions.csv + the original sample CSVs (for full text), writes
spot_check_sample.csv with one row per sampled message. The sample
oversamples the rare cells (where errors are most consequential) and takes
random draws from the dominant cells.

Two caveats worth knowing before relying on this sampler:

  * The 22/24 spot check reported in results.md used 3 draws per common cell,
    not the 10 below, and its per-row labels were never committed. This plan
    generates the committed 52-row spot_check_sample.csv, whose human_p /
    human_e columns are still blank. Filling them in and committing the result
    is what would make that validation claim checkable.
  * Reviewing positive predictions measures precision, not recall. A message
    wrongly coded 0/0 can never enter this sample, so it cannot detect false
    negatives — the error direction the WildChat headline rate is most
    sensitive to. Sampling some predicted-0/0 rows (as the plan does) only
    partly offsets this.

Workflow:
  1. python3 spot_check.py            # generates spot_check_sample.csv
  2. Open in Numbers/Excel/Google Sheets
  3. Read each `text` and fill in `human_p` and `human_e` (0 or 1)
  4. Add notes for any disagreements
  5. Commit the filled-in CSV so the agreement figure is reproducible
"""

import csv
import random
from collections import defaultdict
from pathlib import Path

random.seed(42)

PREDICTIONS_CSV = "predictions.csv"
REDDIT_CSV = "reddit_sample.csv"
WILDCHAT_CSV = "wildchat_sample.csv"
OUTPUT_CSV = "spot_check_sample.csv"

# Per (source, P, E) cell. None means "take all" (used for rare cells).
SAMPLE_PLAN = {
    ("reddit", 0, 0): 10,
    ("reddit", 1, 0): 10,
    ("reddit", 0, 1): None,
    ("reddit", 1, 1): 10,
    ("wildchat", 0, 0): 10,
    ("wildchat", 1, 0): None,
    ("wildchat", 0, 1): None,
    ("wildchat", 1, 1): None,
}


def load_text_by_id() -> dict[str, str]:
    text_by_id = {}
    for path in (REDDIT_CSV, WILDCHAT_CSV):
        if not Path(path).exists():
            raise SystemExit(
                f"{path} not found — needed to attach message text to each sampled row.\n"
                f"The raw samples are not committed to this repo; recreate them from "
                f"Hugging Face using the parameters in data_notes.md."
            )
        with open(path) as f:
            for row in csv.DictReader(f):
                text_by_id[row["id"]] = row["text"]
    return text_by_id


def load_predictions() -> list[dict]:
    rows = []
    with open(PREDICTIONS_CSV) as f:
        for row in csv.DictReader(f):
            row["personal"] = int(row["personal"])
            row["emotional"] = int(row["emotional"])
            rows.append(row)
    return rows


def main():
    if not Path(PREDICTIONS_CSV).exists():
        raise SystemExit(f"{PREDICTIONS_CSV} not found. Run classify_batch.py first.")

    text_by_id = load_text_by_id()
    rows = load_predictions()

    cells = defaultdict(list)
    for r in rows:
        cells[(r["source"], r["personal"], r["emotional"])].append(r)

    sample = []
    print("Stratified sample plan:")
    for key, count in SAMPLE_PLAN.items():
        bucket = cells.get(key, [])
        if count is None or count >= len(bucket):
            picks = bucket
        else:
            picks = random.sample(bucket, count)
        sample.extend(picks)
        print(f"  {key[0]:8} P={key[1]} E={key[2]}: {len(picks):>3} (population: {len(bucket)})")

    # Shuffle so the reviewer doesn't see them grouped (avoids ordering bias).
    random.shuffle(sample)

    fieldnames = [
        "id",
        "source",
        "subreddit",
        "word_count",
        "pred_p",
        "pred_e",
        "pred_reasoning",
        "human_p",
        "human_e",
        "agree",
        "notes",
        "text",
    ]
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sample:
            writer.writerow(
                {
                    "id": r["id"],
                    "source": r["source"],
                    "subreddit": r["subreddit"],
                    "word_count": r["word_count"],
                    "pred_p": r["personal"],
                    "pred_e": r["emotional"],
                    "pred_reasoning": r["reasoning"],
                    "human_p": "",
                    "human_e": "",
                    "agree": "",
                    "notes": "",
                    "text": text_by_id.get(r["id"], "[text missing]"),
                }
            )

    print(f"\nWrote {len(sample)} rows to {OUTPUT_CSV}")
    print("Open in a spreadsheet, fill in human_p / human_e for each row, then share back.")


if __name__ == "__main__":
    main()
