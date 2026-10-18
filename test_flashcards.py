#!/usr/bin/env python3
"""Tests for flashcards.py. Run with: python -m unittest test_flashcards -v"""

import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import flashcards


class ScheduleNextTests(unittest.TestCase):
    def test_correct_answer_moves_up_one_box(self):
        for box in range(1, flashcards.MAX_BOX):
            new_box, _ = flashcards.schedule_next(box, correct=True)
            self.assertEqual(new_box, box + 1)

    def test_correct_answer_caps_at_max_box(self):
        new_box, _ = flashcards.schedule_next(flashcards.MAX_BOX, correct=True)
        self.assertEqual(new_box, flashcards.MAX_BOX)

    def test_wrong_answer_resets_to_box_one(self):
        for box in range(1, flashcards.MAX_BOX + 1):
            new_box, _ = flashcards.schedule_next(box, correct=False)
            self.assertEqual(new_box, 1)

    def test_next_review_interval_matches_destination_box(self):
        for starting_box in flashcards.BOX_INTERVALS:
            new_box, next_review = flashcards.schedule_next(starting_box, correct=True)
            expected = (date.today() + timedelta(days=flashcards.BOX_INTERVALS[new_box])).isoformat()
            self.assertEqual(next_review, expected)

    def test_wrong_answer_next_review_is_tomorrow(self):
        _, next_review = flashcards.schedule_next(3, correct=False)
        expected = (date.today() + timedelta(days=1)).isoformat()
        self.assertEqual(next_review, expected)


class DatabaseBackedTests(unittest.TestCase):
    """Each test gets a fresh in-memory database, never touching the real flashcards.db."""

    def setUp(self):
        self.conn = flashcards.get_connection(":memory:")

    def tearDown(self):
        self.conn.close()

    def test_add_card_defaults_to_box_one_due_today(self):
        flashcards.add_card(self.conn, "arrays", "Q?", "A.")
        row = self.conn.execute("SELECT topic, box, next_review FROM cards").fetchone()
        self.assertEqual(row, ("arrays", 1, flashcards.today_str()))

    def test_due_cards_filters_by_topic(self):
        flashcards.add_card(self.conn, "arrays", "Q1", "A1")
        flashcards.add_card(self.conn, "trees", "Q2", "A2")
        due = flashcards.due_cards(self.conn, topic="trees")
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0][1], "trees")

    def test_edit_card_updates_only_given_fields(self):
        flashcards.add_card(self.conn, "arrays", "Old Q", "Old A")
        card_id = self.conn.execute("SELECT id FROM cards").fetchone()[0]

        flashcards.edit_card(self.conn, card_id, question="New Q")

        topic, question, answer = self.conn.execute(
            "SELECT topic, question, answer FROM cards WHERE id = ?", (card_id,)
        ).fetchone()
        self.assertEqual(topic, "arrays")
        self.assertEqual(question, "New Q")
        self.assertEqual(answer, "Old A")

    def test_edit_card_missing_id_exits(self):
        with self.assertRaises(SystemExit):
            flashcards.edit_card(self.conn, 999, question="New Q")

    def test_delete_card_removes_row(self):
        flashcards.add_card(self.conn, "arrays", "Q", "A")
        card_id = self.conn.execute("SELECT id FROM cards").fetchone()[0]

        flashcards.delete_card(self.conn, card_id, skip_confirm=True)

        remaining = self.conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        self.assertEqual(remaining, 0)

    def test_delete_card_missing_id_exits(self):
        with self.assertRaises(SystemExit):
            flashcards.delete_card(self.conn, 999, skip_confirm=True)

    def test_import_valid_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "cards.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["topic", "question", "answer"])
                writer.writerow(["arrays", "Q1", "A1"])
                writer.writerow(["trees", "Q2", "A2"])

            flashcards.import_cards(self.conn, str(csv_path))

            count = self.conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
            self.assertEqual(count, 2)

    def test_import_skips_rows_with_missing_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "cards.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["topic", "question", "answer"])
                writer.writerow(["arrays", "Q1", "A1"])
                writer.writerow(["arrays", "", "A2"])  # missing question

            flashcards.import_cards(self.conn, str(csv_path))

            count = self.conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
            self.assertEqual(count, 1)

    def test_import_missing_column_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "cards.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["topic", "question"])  # no "answer" column
                writer.writerow(["arrays", "Q1"])

            with self.assertRaises(SystemExit):
                flashcards.import_cards(self.conn, str(csv_path))

    def test_import_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            flashcards.import_cards(self.conn, "does_not_exist.csv")


if __name__ == "__main__":
    unittest.main()
