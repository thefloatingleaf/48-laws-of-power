# 48 Laws of Power

Standalone daily learning generator for your iPhone Shortcut. This repo publishes one plain-text file online every day, and your Shortcut can fetch that raw file URL and forward it to WhatsApp at 9:00 AM.

## What it does

- Generates `daily_learning.txt` with this exact format:

```text
Today's Learning from 48 Laws of Power:

<one law here>
```

- Picks from the 48 laws you provided.
- Picks a random law, but blocks any law from repeating until ten other distinct laws have each been shown at least twice.
- Saves scheduling state in `learning_state.json`.
- Saves a published send history in `history.json`.
- Publishes the latest text file automatically through GitHub Actions at `03:00 Asia/Kolkata`.

## Repeat rule

The repeat rule is:

1. A law can appear for the first time at random.
2. Once it has appeared, it cannot become eligible again immediately.
3. It only becomes eligible again after at least ten other distinct laws have each reached two total appearances in history.
4. If multiple laws are eligible, the selection stays random.

## Repo structure

- `generate_daily_law.py`: main generator
- `laws.json`: source list of 48 laws
- `learning_state.json`: generated state file
- `daily_learning.txt`: published output file
- `history.json`: published day-by-day archive
- `scripts/setup.sh`: one-command environment check
- `scripts/generate-daily-learning.sh`: one-command generate + verify script
- `scripts/test.sh`: one-command test runner
- `scripts/verify_daily_learning.py`: consistency check
- `tests/test_generate_daily_law.py`: smoke tests for repeat behavior
- `.github/workflows/daily-learning.yml`: daily publish workflow

## Prerequisites

- macOS
- `python3` available in Terminal
- `git`
- `gh` optional, but recommended for creating and pushing the GitHub repo

## One-command setup

```bash
./scripts/setup.sh
```

## One-command local run

```bash
./scripts/generate-daily-learning.sh
```

Expected result:

- `daily_learning.txt` is created or refreshed
- `learning_state.json` is created or refreshed
- the script exits without error

If it fails, likely causes are:

1. `python3: command not found`
   Fix: install Python 3 and rerun.
2. `Permission denied` on the script
   Fix: run `chmod +x scripts/generate-daily-learning.sh` once, then rerun.

## One-command tests

```bash
./scripts/test.sh
```

## Date simulation

To simulate a specific day safely:

```bash
LAWS48_NOW_DATE=2026-04-23 ./scripts/generate-daily-learning.sh
```

## Publish flow

Once pushed to GitHub, the workflow:

1. Runs every day at `03:00 Asia/Kolkata`.
2. Runs backup refreshes again at `05:00` and `07:00 Asia/Kolkata`.
3. Regenerates `daily_learning.txt`.
4. Verifies the output.
5. Commits and pushes the refreshed `daily_learning.txt`, `learning_state.json`, and `history.json`.

## iPhone Shortcut setup

Use this in your Shortcut:

1. Add `Get Contents of URL`.
2. Paste the raw GitHub URL for `daily_learning.txt`.
3. Feed that text into your WhatsApp send step.
4. Keep your Shortcut trigger at `09:00 AM`.

Raw URL format after GitHub publish:

```text
https://raw.githubusercontent.com/<github-username>/<repo-name>/main/daily_learning.txt
```

## Troubleshooting

If the same law does not look right:

1. Check `learning_state.json` for `current_law` and `current_law_total_appearances`.
2. Check `history.json` to confirm what was published on prior dates.
3. Run the tests.
4. If needed, simulate dates with `LAWS48_NOW_DATE` to verify repeat eligibility.
