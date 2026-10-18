#!/usr/bin/env python3
"""DSA flashcard CLI using Leitner spaced repetition. Stdlib only."""

import argparse
import csv
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "flashcards.db"
REQUIRED_CSV_COLUMNS = {"topic", "question", "answer"}

# Box N -> days until the card is due again after a correct answer.
BOX_INTERVALS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
MAX_BOX = max(BOX_INTERVALS)


def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            box INTEGER NOT NULL DEFAULT 1,
            next_review TEXT NOT NULL
        )
        """
    )
    return conn


def today_str():
    return date.today().isoformat()


def add_card(conn, topic, question, answer):
    conn.execute(
        "INSERT INTO cards (topic, question, answer, box, next_review) VALUES (?, ?, ?, 1, ?)",
        (topic, question, answer, today_str()),
    )
    conn.commit()
    print(f"Added card for topic '{topic}', due today in box 1.")


def get_card(conn, card_id):
    return conn.execute(
        "SELECT id, topic, question, answer, box, next_review FROM cards WHERE id = ?",
        (card_id,),
    ).fetchone()


def edit_card(conn, card_id, topic=None, question=None, answer=None):
    card = get_card(conn, card_id)
    if card is None:
        print(f"No card found with id {card_id}.")
        sys.exit(1)

    new_topic = topic if topic is not None else card[1]
    new_question = question if question is not None else card[2]
    new_answer = answer if answer is not None else card[3]

    conn.execute(
        "UPDATE cards SET topic = ?, question = ?, answer = ? WHERE id = ?",
        (new_topic, new_question, new_answer, card_id),
    )
    conn.commit()
    print(f"Updated card #{card_id}.")


def delete_card(conn, card_id, skip_confirm=False):
    card = get_card(conn, card_id)
    if card is None:
        print(f"No card found with id {card_id}.")
        sys.exit(1)

    _, topic, question, *_ = card
    if not skip_confirm:
        preview = question if len(question) <= 60 else question[:57] + "..."
        reply = input(f"Delete card #{card_id} [{topic}] \"{preview}\"? (y/n): ").strip().lower()
        if not reply.startswith("y"):
            print("Cancelled.")
            return

    conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    print(f"Deleted card #{card_id}.")


def import_cards(conn, csv_path):
    path = Path(csv_path)
    if not path.exists():
        print(f"File not found: {csv_path}")
        sys.exit(1)

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        missing = REQUIRED_CSV_COLUMNS - fieldnames
        if missing:
            print(
                f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
                f"Expected a header with: topic,question,answer"
            )
            sys.exit(1)

        count = 0
        skipped = 0
        for line_num, row in enumerate(reader, start=2):
            topic = (row.get("topic") or "").strip()
            question = (row.get("question") or "").strip()
            answer = (row.get("answer") or "").strip()
            if not topic or not question or not answer:
                print(f"Skipping row {line_num}: missing topic, question, or answer.")
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO cards (topic, question, answer, box, next_review) VALUES (?, ?, ?, 1, ?)",
                (topic, question, answer, today_str()),
            )
            count += 1

    conn.commit()
    print(f"Imported {count} cards from {csv_path}.")
    if skipped:
        print(f"Skipped {skipped} invalid row(s).")
    return count, skipped


def due_cards(conn, topic=None):
    query = "SELECT id, topic, question, answer, box FROM cards WHERE next_review <= ?"
    params = [today_str()]
    if topic:
        query += " AND topic = ?"
        params.append(topic)
    query += " ORDER BY box, id"
    return conn.execute(query, params).fetchall()


def schedule_next(box, correct):
    """Return the new box after an answer. Correct moves up, wrong resets to box 1."""
    if correct:
        new_box = min(box + 1, MAX_BOX)
    else:
        new_box = 1
    next_review = date.today() + timedelta(days=BOX_INTERVALS[new_box])
    return new_box, next_review.isoformat()


def review(conn, topic=None):
    cards = due_cards(conn, topic)
    if not cards:
        scope = f" for topic '{topic}'" if topic else ""
        print(f"No cards due today{scope}. Nice work.")
        return

    correct_count = 0
    wrong_count = 0

    for card_id, card_topic, question, answer, box in cards:
        print(f"\n[{card_topic}] (box {box})")
        print(f"Q: {question}")
        input("Press Enter to reveal the answer...")
        print(f"A: {answer}")

        reply = input("Got it? (y/n): ").strip().lower()
        correct = reply.startswith("y")

        new_box, next_review = schedule_next(box, correct)
        conn.execute(
            "UPDATE cards SET box = ?, next_review = ? WHERE id = ?",
            (new_box, next_review, card_id),
        )
        conn.commit()

        if correct:
            correct_count += 1
            print(f"Moved to box {new_box}, next review on {next_review}.")
        else:
            wrong_count += 1
            print(f"Reset to box {new_box}, next review on {next_review}.")

    total = correct_count + wrong_count
    print(f"\nSession complete: {correct_count}/{total} correct, {wrong_count}/{total} wrong.")


def stats(conn):
    total = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    due_today = conn.execute(
        "SELECT COUNT(*) FROM cards WHERE next_review <= ?", (today_str(),)
    ).fetchone()[0]

    print(f"Total cards: {total}")
    print(f"Due today: {due_today}")
    print("Cards per box:")
    for box in sorted(BOX_INTERVALS):
        count = conn.execute(
            "SELECT COUNT(*) FROM cards WHERE box = ?", (box,)
        ).fetchone()[0]
        print(f"  Box {box} (every {BOX_INTERVALS[box]}d): {count}")


def list_cards(conn, topic=None):
    query = "SELECT id, topic, question, box, next_review FROM cards"
    params = []
    if topic:
        query += " WHERE topic = ?"
        params.append(topic)
    query += " ORDER BY topic, id"

    rows = conn.execute(query, params).fetchall()
    if not rows:
        print("No cards found.")
        return

    for card_id, card_topic, question, box, next_review in rows:
        preview = question if len(question) <= 60 else question[:57] + "..."
        print(f"#{card_id} [{card_topic}] box {box}, due {next_review}: {preview}")


def build_parser():
    parser = argparse.ArgumentParser(
        description="DSA flashcard CLI using Leitner spaced repetition."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a single card")
    add_parser.add_argument("--topic", required=True)
    add_parser.add_argument("--question", required=True)
    add_parser.add_argument("--answer", required=True)

    import_parser = subparsers.add_parser("import", help="Import cards from a CSV file")
    import_parser.add_argument("csv_path", help="Path to a CSV with topic,question,answer columns")

    edit_parser = subparsers.add_parser("edit", help="Edit an existing card")
    edit_parser.add_argument("id", type=int, help="Card id (see 'list')")
    edit_parser.add_argument("--topic")
    edit_parser.add_argument("--question")
    edit_parser.add_argument("--answer")

    delete_parser = subparsers.add_parser("delete", help="Delete a card")
    delete_parser.add_argument("id", type=int, help="Card id (see 'list')")
    delete_parser.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt"
    )

    review_parser = subparsers.add_parser("review", help="Review today's due cards")
    review_parser.add_argument("--topic", help="Only review cards for this topic")

    subparsers.add_parser("stats", help="Show totals, due count, and per-box counts")

    list_parser = subparsers.add_parser("list", help="List all cards with box and next review date")
    list_parser.add_argument("--topic", help="Only list cards for this topic")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    conn = get_connection()
    try:
        if args.command == "add":
            add_card(conn, args.topic, args.question, args.answer)
        elif args.command == "import":
            import_cards(conn, args.csv_path)
        elif args.command == "edit":
            edit_card(conn, args.id, args.topic, args.question, args.answer)
        elif args.command == "delete":
            delete_card(conn, args.id, skip_confirm=args.yes)
        elif args.command == "review":
            review(conn, args.topic)
        elif args.command == "stats":
            stats(conn)
        elif args.command == "list":
            list_cards(conn, args.topic)
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Progress on any answered cards was already saved.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
