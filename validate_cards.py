#!/usr/bin/env python3
"""Validate a flashcards CSV before it's merged.

Checks structure/blank fields (by reusing flashcards.import_cards against a
throwaway in-memory database) and flags questions that are near-duplicates
of each other.

Run locally before opening a PR:
    python validate_cards.py cards.csv

Also run automatically on every pull request by
.github/workflows/validate-cards.yml.
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import flashcards

normalize = flashcards.normalize_question


def find_duplicate_questions(csv_path):
    """Return {normalized_question: [(line_number, original_question), ...]} for duplicates."""
    seen = defaultdict(list)
    with Path(csv_path).open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_num, row in enumerate(reader, start=2):
            question = (row.get("question") or "").strip()
            if question:
                seen[normalize(question)].append((line_num, question))
    return {key: rows for key, rows in seen.items() if len(rows) > 1}


def main():
    parser = argparse.ArgumentParser(description="Validate a flashcards CSV before merging.")
    parser.add_argument("csv_path", nargs="?", default="cards.csv")
    args = parser.parse_args()

    conn = flashcards.get_connection(":memory:")
    imported, skipped, _in_batch_duplicates = flashcards.import_cards(conn, args.csv_path)
    conn.close()

    duplicates = find_duplicate_questions(args.csv_path)

    ok = True
    if skipped:
        print(f"\nFAIL: {skipped} row(s) are missing a topic, question, or answer.")
        ok = False

    if duplicates:
        print(f"\nFAIL: {len(duplicates)} question(s) appear more than once:")
        for rows in duplicates.values():
            locations = ", ".join(f"line {line}" for line, _ in rows)
            print(f'  - "{rows[0][1]}" ({locations})')
        ok = False

    if ok:
        print(f"\nOK: {imported} cards validated, no duplicates found.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
