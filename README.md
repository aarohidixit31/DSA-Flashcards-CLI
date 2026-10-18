# DSA Flashcards CLI

A terminal app for revising DSA using Leitner spaced repetition. Cards you
answer correctly get reviewed less often over time, and cards you miss
return to daily review.

Python standard library only — no installs needed. Cards are stored in a
local SQLite database (`flashcards.db`), created automatically on first run.

## How it works

There are five Leitner boxes with increasing review gaps:

| Box | Review interval |
|-----|------------------|
| 1   | 1 day            |
| 2   | 2 days           |
| 3   | 4 days           |
| 4   | 8 days           |
| 5   | 16 days          |

New cards start in box 1 and are due today. Answering a card correctly
during review moves it up one box (longer gap before it's due again).
Answering incorrectly resets it to box 1 (due again tomorrow).

## Usage

Add a card:

```
python flashcards.py add --topic arrays --question "What is the time complexity of binary search?" --answer "O(log n)"
```

Import cards from a CSV (columns: `topic,question,answer`):

```
python flashcards.py import cards.csv
```

Review today's due cards:

```
python flashcards.py review
```

Review only one topic:

```
python flashcards.py review --topic trees
```

Show stats (total cards, due today, cards per box):

```
python flashcards.py stats
```

List all cards with their box and next review date:

```
python flashcards.py list
python flashcards.py list --topic strings
```

Edit a card (use the id shown by `list`; only the fields you pass are changed):

```
python flashcards.py edit 3 --answer "Updated answer text"
```

Delete a card (asks for confirmation; pass `--yes` to skip it):

```
python flashcards.py delete 3
python flashcards.py delete 3 --yes
```

## Running the tests

`test_flashcards.py` covers the Leitner scheduling math (box transitions,
interval calculation) and the edit/delete/import logic against a throwaway
in-memory database — it never touches your real `flashcards.db`:

```
python -m unittest test_flashcards -v
```

## Example session

```
$ python flashcards.py import cards.csv
Imported 15 cards from cards.csv.

$ python flashcards.py review --topic arrays
[arrays] (box 1)
Q: What is the time complexity of accessing an element by index in an array?
Press Enter to reveal the answer...
A: O(1) because arrays use contiguous memory and direct offset calculation
Got it? (y/n): y
Moved to box 2, next review on 2026-10-21.
...
Session complete: 5/6 correct, 1/6 wrong.

$ python flashcards.py stats
Total cards: 15
Due today: 0
Cards per box:
  Box 1 (every 1d): 1
  Box 2 (every 2d): 14
  Box 3 (every 4d): 0
  Box 4 (every 8d): 0
  Box 5 (every 16d): 0
```
