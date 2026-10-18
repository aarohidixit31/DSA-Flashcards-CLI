# Contributing

Thanks for wanting to add DSA questions! This project is a shared flashcard
deck: the more good questions it has, the more useful it is for everyone
revising from it.

## Adding questions

1. Open [`cards.csv`](cards.csv). It has three columns: `topic`, `question`, `answer`.
2. Add your rows at the end of the file. Try to keep one topic per PR,
   it's easier to review than a big mixed batch.
3. If a question or answer contains a comma, wrap that whole field in double
   quotes so it isn't split into extra columns:

   ```csv
   arrays,What is the time complexity of inserting at the start of an array?,"O(n), because every element must shift"
   ```

4. Use an existing topic where it fits (`arrays`, `strings`, `trees`,
   `linked-lists`, `stacks`, `queues`, `graphs`, `sorting`, `recursion`,
   `dynamic-programming`, `hashing`) or a new lowercase, hyphenated topic
   name if it genuinely doesn't fit any of those.
5. Keep answers short and correct: a sentence or two, like the existing
   cards. This is a revision aid, not a textbook.

## Before opening a PR

Run the validator locally. It's the same check that runs in CI, so this
tells you up front whether your PR will pass:

```bash
python validate_cards.py cards.csv
```

It checks for:
- missing `topic`/`question`/`answer` values
- questions that are near-duplicates of ones already in the file (so the
  same question doesn't get added twice)

If you're adding new app features rather than questions, also run the test
suite:

```bash
python -m unittest discover -v
```

## What happens after you open a PR

A GitHub Action automatically runs `validate_cards.py` and the test suite
on every PR. If that check fails, fix what it reports and push again.
There's no need to wait for a manual review to find out your CSV is broken.
Once the check passes, a maintainer will review the actual content (is the
answer correct, is it a useful question) and merge.

By submitting a PR, you agree your contribution is licensed under this
repo's [MIT License](LICENSE).
