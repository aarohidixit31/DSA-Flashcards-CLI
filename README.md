# DSA Flashcards CLI

A terminal app for revising data structures & algorithms using **Leitner
spaced repetition**: cards you get right are shown less often, cards you miss
come back the next day. No installs, no server, no account — just Python's
standard library and a local SQLite file.

```
$ python flashcards.py review --topic trees
[trees] (box 1)
Q: What is the time complexity of searching in a balanced binary search tree?
Press Enter to reveal the answer...
A: O(log n) because the height of a balanced BST is log n
Got it? (y/n): y
Moved to box 2, next review on 2026-10-21.
```

## Why this exists

Re-reading your DSA notes the night before an interview doesn't make things
stick — you need to be quizzed on them *repeatedly, over time*, and spend
more time on what you actually get wrong. That's spaced repetition, and the
**Leitner system** is the simplest version of it: a fixed set of "boxes"
with increasing review gaps, where a correct answer promotes a card to a
longer gap and a wrong answer demotes it back to daily review.

This project is also meant to be *readable end to end* — the whole app is
one file, under 300 lines, with no frameworks or dependencies in the way. If
you want to learn how spaced repetition is actually implemented (not just
what it is), reading `flashcards.py` top to bottom should be enough.

## Requirements

- Python 3.8 or newer
- Nothing else — no `pip install`, no external packages. Everything used
  (`argparse`, `csv`, `sqlite3`) is in the standard library.

## Getting started

```bash
git clone https://github.com/aarohidixit31/DSA-Flashcards-CLI.git
cd DSA-Flashcards-CLI
python flashcards.py import cards.csv   # loads the 50 starter cards
python flashcards.py review             # start your first review session
```

A `flashcards.db` SQLite file is created automatically next to the script on
first run — you never create or touch it directly.

## Commands

| Command | What it does |
|---|---|
| `add --topic T --question Q --answer A` | Add a single new card (starts in box 1, due today) |
| `import <file.csv>` | Bulk-load cards from a CSV with `topic,question,answer` columns |
| `review [--topic T]` | Review all cards due today, optionally filtered to one topic |
| `edit <id> [--topic] [--question] [--answer]` | Update one or more fields of an existing card |
| `delete <id> [--yes]` | Delete a card (asks for confirmation unless `--yes` is passed) |
| `list [--topic T]` | Show every card with its id, box, and next review date |
| `stats` | Show total cards, cards due today, and how many are in each box |

Examples:

```bash
python flashcards.py add --topic graphs --question "What does BFS use to visit nodes in order?" --answer "A queue"
python flashcards.py review --topic arrays
python flashcards.py edit 12 --answer "O(n log n) average, O(n^2) worst case"
python flashcards.py delete 12 --yes
python flashcards.py list --topic strings
python flashcards.py stats
```

## How the Leitner scheduling works

There are five boxes, each with a longer review gap than the last:

| Box | Review interval | Meaning |
|-----|------------------|---------|
| 1   | 1 day            | New or recently-missed cards |
| 2   | 2 days           | Answered correctly once |
| 3   | 4 days           | Answered correctly a few times |
| 4   | 8 days           | Well known |
| 5   | 16 days          | Mastered — rarely needs review |

The rule is simple:
- **Correct answer** → move up one box (longer gap before it's due again), capped at box 5.
- **Wrong answer** → reset to box 1 (due again tomorrow).

New cards always start in box 1, due immediately. The entire scheduling
logic is one small function, `schedule_next()` in `flashcards.py` — worth
reading first if you're curious how the rest of the app fits together.

## Project structure

```
flashcards.py                      the CLI: argument parsing, SQLite storage, review loop
test_flashcards.py                 unit tests for the scheduling math and edit/delete/import logic
validate_cards.py                  validates cards.csv (structure + duplicate questions) before a PR is merged
cards.csv                          50 starter DSA questions across 11 topics
flashcards.db                      created automatically on first run (not committed — see .gitignore)
.github/workflows/validate.yml     CI: runs the tests and validate_cards.py on every PR
.gitignore                         ignores flashcards.db and Python cache files
LICENSE                            MIT
CONTRIBUTING.md                    how to submit new questions via PR
```

## Importing your own cards

`cards.csv` is a plain CSV with a `topic,question,answer` header — open it in
any editor or spreadsheet app to see the format. To add your own:

- **One at a time:** `python flashcards.py add --topic ... --question ... --answer ...`
- **In bulk:** add rows to a CSV (same three columns) and run
  `python flashcards.py import your_file.csv`

If a question or answer contains a comma, wrap that field in double quotes
(`"like this, with a comma"`) so the CSV parser doesn't split it into extra
columns — `import` will tell you exactly which row it skipped and why if a
row is malformed.

Note: `import` always appends and does not check for duplicates. Re-running
`import cards.csv` on a database that already has those cards will create
copies — only re-import after deleting `flashcards.db`, or when adding
genuinely new rows.

## Contributing questions

Pull requests adding new DSA questions to `cards.csv` are welcome — see
[CONTRIBUTING.md](CONTRIBUTING.md) for the format and how to validate your
additions locally before opening a PR. Every PR is automatically checked by
a GitHub Action (`validate_cards.py` + the test suite) for structural
issues and duplicate questions before it's reviewed for content.

## Running the tests

`test_flashcards.py` covers the Leitner scheduling math (box transitions,
interval calculation) and the edit/delete/import logic, all against a
throwaway in-memory database — it never touches your real `flashcards.db`.
`test_validate_cards.py` covers the duplicate-question check. Run both with:

```bash
python -m unittest discover -v
```

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, adapt it for your own
revision topics.
