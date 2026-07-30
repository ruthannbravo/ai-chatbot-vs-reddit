"""
Run the LLM classifier on all ~3,000 messages (1,500 Reddit + 1,500 WildChat)
via the Anthropic Message Batches API. ~50% cost vs. real-time, completes
within an hour for jobs this size.

Writes predictions to predictions.csv (atomically — the existing file is only
replaced once a run has produced at least one usable row), any per-row failures
to errors.csv, and the batch ID to batch_state.json so polling can resume after
an interruption.

Usage:
    python3 classify_batch.py            # submit a new batch and wait for results
    python3 classify_batch.py --resume   # resume polling the batch in batch_state.json

Note: the API keeps batch results retrievable for 29 days. After that, --resume
cannot recover anything and a fresh submission is required.
"""

import argparse
import csv
import json
import os
import sys
import tempfile
import time
from pathlib import Path

from anthropic import Anthropic, APIStatusError
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from classify import CODEBOOK, MODEL, SCHEMA  # share the codebook + schema

REDDIT_CSV = "reddit_sample.csv"
WILDCHAT_CSV = "wildchat_sample.csv"
STATE_FILE = "batch_state.json"
PREDICTIONS_CSV = "predictions.csv"
ERRORS_CSV = "errors.csv"
POLL_INTERVAL_SEC = 60
POLL_TIMEOUT_SEC = 6 * 60 * 60  # give up after 6h; batches this size finish in ~1h


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
        if not Path(path).exists():
            raise SystemExit(
                f"{path} not found. The raw samples are not committed to this repo — "
                f"recreate them from Hugging Face using the parameters in data_notes.md."
            )
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
    state = {"batch_id": batch.id, "submitted_at": time.time(), "rows": row_meta}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print(f"State saved to {STATE_FILE}")
    return batch.id, row_meta


def poll_until_done(client: Anthropic, batch_id: str):
    deadline = time.monotonic() + POLL_TIMEOUT_SEC
    while True:
        try:
            batch = client.messages.batches.retrieve(batch_id)
        except APIStatusError as exc:
            if exc.status_code == 404:
                raise SystemExit(
                    f"Batch {batch_id} was not found. Results are retrievable for only "
                    f"29 days after creation, so this batch has most likely expired.\n"
                    f"Delete {STATE_FILE} and re-run without --resume to submit a new batch."
                ) from exc
            raise
        rc = batch.request_counts
        print(
            f"[{time.strftime('%H:%M:%S')}] status={batch.processing_status}  "
            f"succeeded={rc.succeeded} processing={rc.processing} "
            f"errored={rc.errored} expired={rc.expired} canceled={rc.canceled}"
        )
        if batch.processing_status == "ended":
            return batch
        if time.monotonic() > deadline:
            raise SystemExit(
                f"Batch {batch_id} still not ended after {POLL_TIMEOUT_SEC // 3600}h. "
                f"State is preserved in {STATE_FILE}; re-run with --resume to keep waiting."
            )
        time.sleep(POLL_INTERVAL_SEC)


def parse_label(parsed: dict, key: str) -> int:
    """Return parsed[key] as 0 or 1, or raise ValueError. Guards against a
    malformed object writing an empty cell that every downstream int() would
    choke on."""
    value = parsed[key]  # KeyError if absent
    if isinstance(value, bool) or not isinstance(value, int):
        value = int(str(value).strip())  # ValueError on anything non-numeric
    if value not in (0, 1):
        raise ValueError(f"{key}={value!r} outside (0, 1)")
    return value


def collect_results(client: Anthropic, batch_id: str, row_meta: dict):
    succeeded = 0
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

    # Write to a sibling temp file and only replace predictions.csv once the run
    # has produced usable rows, so a mid-stream failure can't destroy the
    # existing dataset.
    out_dir = Path(PREDICTIONS_CSV).resolve().parent
    fd, tmp_path = tempfile.mkstemp(dir=out_dir, prefix=".predictions-", suffix=".csv")
    try:
        with os.fdopen(fd, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in client.messages.batches.results(batch_id):
                rid = result.custom_id
                meta = row_meta.get(rid, {})

                if result.result.type != "succeeded":
                    error_log.append((rid, result.result.type, ""))
                    continue

                msg = result.result.message
                stop_reason = getattr(msg, "stop_reason", "") or ""
                text = next((b.text for b in msg.content if b.type == "text"), None)
                if text is None:
                    error_log.append((rid, "no_text_block", stop_reason))
                    continue
                try:
                    parsed = json.loads(text)
                    personal = parse_label(parsed, "personal")
                    emotional = parse_label(parsed, "emotional")
                except (json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError) as exc:
                    error_log.append((rid, f"bad_label:{type(exc).__name__}", stop_reason))
                    continue

                writer.writerow(
                    {
                        "id": rid,
                        "source": meta.get("source", ""),
                        "subreddit": meta.get("subreddit", ""),
                        "word_count": meta.get("word_count", ""),
                        "personal": personal,
                        "emotional": emotional,
                        "reasoning": parsed.get("reasoning", ""),
                    }
                )
                succeeded += 1

        if succeeded == 0:
            raise SystemExit(
                f"No usable predictions were parsed from batch {batch_id}; "
                f"leaving the existing {PREDICTIONS_CSV} untouched. "
                f"See {ERRORS_CSV} for per-row reasons."
            )
        os.replace(tmp_path, PREDICTIONS_CSV)
        tmp_path = None
    finally:
        if tmp_path is not None:
            Path(tmp_path).unlink(missing_ok=True)
        write_error_log(error_log)

    print(f"\nWrote {succeeded} predictions to {PREDICTIONS_CSV}")
    if error_log:
        print(f"{len(error_log)} requests did not yield a usable prediction (see {ERRORS_CSV}):")
        for rid, why, stop_reason in error_log[:20]:
            print(f"  {rid}: {why}" + (f" (stop_reason={stop_reason})" if stop_reason else ""))
        if len(error_log) > 20:
            print(f"  ... and {len(error_log) - 20} more")


def write_error_log(error_log: list[tuple[str, str, str]]) -> None:
    """Persist failures so counts quoted in the writeup are an artifact, not a memory."""
    if not error_log:
        return
    with open(ERRORS_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "reason", "stop_reason"])
        writer.writerows(error_log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--resume",
        action="store_true",
        help=f"resume polling the batch recorded in {STATE_FILE} instead of submitting a new one",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set.")

    client = Anthropic()

    if args.resume:
        if not Path(STATE_FILE).exists():
            sys.exit(f"--resume given but {STATE_FILE} does not exist. Re-run without --resume.")
        with open(STATE_FILE) as f:
            state = json.load(f)
        batch_id = state["batch_id"]
        row_meta = state["rows"]
        print(f"Resuming batch {batch_id} from {STATE_FILE}")
    else:
        if Path(STATE_FILE).exists():
            sys.exit(
                f"{STATE_FILE} already exists, describing a previously submitted batch.\n"
                f"  To resume that batch:      python3 classify_batch.py --resume\n"
                f"  To submit a fresh batch:   rm {STATE_FILE} && python3 classify_batch.py"
            )
        batch_id, row_meta = submit_batch(client)

    poll_until_done(client, batch_id)
    collect_results(client, batch_id, row_meta)


if __name__ == "__main__":
    main()
