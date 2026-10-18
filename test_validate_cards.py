#!/usr/bin/env python3
"""Tests for validate_cards.py. Run with: python -m unittest test_validate_cards -v"""

import csv
import tempfile
import unittest
from pathlib import Path

import validate_cards


class NormalizeTests(unittest.TestCase):
    def test_lowercases_and_collapses_whitespace(self):
        self.assertEqual(
            validate_cards.normalize("  What IS   Big-O  of   BFS?  "),
            "what is big-o of bfs?",
        )


class FindDuplicateQuestionsTests(unittest.TestCase):
    def _write_csv(self, rows):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", newline="", encoding="utf-8", suffix=".csv", delete=False
        )
        writer = csv.writer(tmp)
        writer.writerow(["topic", "question", "answer"])
        writer.writerows(rows)
        tmp.close()
        return Path(tmp.name)

    def test_no_duplicates_returns_empty(self):
        path = self._write_csv(
            [
                ["arrays", "Q1?", "A1"],
                ["trees", "Q2?", "A2"],
            ]
        )
        try:
            self.assertEqual(validate_cards.find_duplicate_questions(path), {})
        finally:
            path.unlink()

    def test_detects_duplicate_ignoring_case_and_whitespace(self):
        path = self._write_csv(
            [
                ["arrays", "What is Big-O of BFS?", "A1"],
                ["trees", "  what is big-o   of bfs?  ", "A2"],
            ]
        )
        try:
            duplicates = validate_cards.find_duplicate_questions(path)
            self.assertEqual(len(duplicates), 1)
            [(rows)] = duplicates.values()
            self.assertEqual([line for line, _ in rows], [2, 3])
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
