"""
Run the LLM classifier on all 3,000 messages (1,500 Reddit + 1,500 WildChat)
via the Anthropic Message Batches API. ~50% cost vs. real-time, completes
within an hour for jobs this size.

Saves the batch ID to batch_state.json so polling can resume after a kill.
Writes predictions to predictions.csv.

Usage:
    python3 classify_batch.py        # submit (or resume) and wait for results
    rm batch_state.json              # clear state to re-submit a new batch
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

from anthropic import Anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from classify import CODEBOOK, MODEL, SCHEMA  # share the codebook + schema

REDDIT_CSV = "reddit_sample.csv"
WILDCHAT_CSV = "wildchat_sample.csv"
STATE_FILE = "batch_state.json"
PREDICTIONS_CSV = "predictions.csv"
POLL_INTERVAL_SEC = 60


def build_request(row: dict) -> Request:
    return Request(
        custom_id=row["id"],
        params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": CODEBOOK,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"Classify this message:\n\n<message>\n{row['text']}\n</message>",
                }
            ],
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        ),
    )


def submit_batch(client: Anthropic) -> tuple[str, dict]:
    raw_rows = []
    for path in (REDDIT_CSV, WILDCHAT_CSV):
        with open(path) as f:
            raw_rows.extend(csv.DictReader(f))
    print(f"Loaded {len(raw_rows)} rows ({REDDIT_CSV} + {WILDCHAT_CSV})")

    # Batch API requires unique custom_id per request. wildchat_sample.csv has
    # 3 exact-duplicate rows — keep first occurrence, drop the rest.
    rows = []
    seen = set()
    for r in raw_rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        rows.append(r)
    dropped = len(raw_rows) - len(rows)
    if dropped:
        print(f"Dropped {dropped} duplicate-id rows; {len(rows)} unique requests")

    requests = [build_request(r) for r in rows]
    print(f"Submitting batch of {len(requests)} requests with {MODEL}...")
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch ID: {batch.id}")
    print(f"Initial status: {batch.processing_status}")

    row_meta = {
        r["id"]: {
            "source": r["source"],
            "subreddit": r.get("subreddit", "") or "",
            "word_count": r.get("word_count", "") or "",
        }
        for r in rows
    }
    state = {"batch_id": batch.id, "rows": row_meta}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print(f"State saved to {STATE_FILE}")
    return batch.id, row_meta


def poll_until_done(client: Anthropic, batch_id: str):
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        rc = batch.request_counts
        print(
            f"[{time.strftime('%H:%M:%S')}] status={batch.processing_status}  "
            f"succeeded={rc.succeeded} processing={rc.processing} "
            f"errored={rc.errored} expired={rc.expired} canceled={rc.canceled}"
        )
        if batch.processing_status == "ended":
            return batch
        time.sleep(POLL_INTERVAL_SEC)


def collect_results(client: Anthropic, batch_id: str, row_meta: dict):
    succeeded = errored = 0
    error_log = []

    fieldnames = [
        "id",
        "source",
        "subreddit",
        "word_count",
        "personal",
        "emotional",
        "reasoning",
    ]
    with open(PREDICTIONS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in client.messages.batches.results(batch_id):
            rid = result.custom_id
            meta = row_meta.get(rid, {})

            if result.result.type != "succeeded":
                errored += 1
                error_log.append((rid, result.result.type))
                continue

            msg = result.result.message
            text = next((b.text for b in msg.content if b.type == "text"), None)
            if text is None:
                errored += 1
                error_log.append((rid, "no_text_block"))
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                errored += 1
                error_log.append((rid, "json_parse_error"))
                continue

            writer.writerow(
                {
                    "id": rid,
                    "source": meta.get("source", ""),
                    "subreddit": meta.get("subreddit", ""),
                    "word_count": meta.get("word_count", ""),
                    "personal": parsed.get("personal"),
                    "emotional": parsed.get("emotional"),
                    "reasoning": parsed.get("reasoning", ""),
                }
            )
            succeeded += 1

    print(f"\nWrote {succeeded} predictions to {PREDICTIONS_CSV}")
    if errored:
        print(f"\n{errored} requests did not yield a usable prediction:")
        for rid, why in error_log[:20]:
            print(f"  {rid}: {why}")
        if len(error_log) > 20:
            print(f"  ... and {len(error_log) - 20} more")


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set.")

    client = Anthropic()

    if Path(STATE_FILE).exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
        batch_id = state["batch_id"]
        row_meta = state["rows"]
        print(f"Resuming batch {batch_id} from {STATE_FILE}")
        print(f"(Delete {STATE_FILE} to submit a fresh batch.)")
    else:
        batch_id, row_meta = submit_batch(client)

    poll_until_done(client, batch_id)
    collect_results(client, batch_id, row_meta)


if __name__ == "__main__":
    main()
