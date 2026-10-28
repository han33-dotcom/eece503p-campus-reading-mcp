"""Domain functions shared by tools. No MCP registration in this module."""
from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent


class LibraryError(ValueError):
    """Predictable domain failure; safe to return to a caller."""


class Book(BaseModel):
    book_id: str
    title: str
    author: str
    subjects: list[str]


class SearchResult(BaseModel):
    query: str
    count: int
    books: list[Book]


class SaveResult(BaseModel):
    status: Literal["saved", "already_saved"]
    list_name: str
    book: Book
    saved_at: str


class PlanResult(BaseModel):
    query: str
    selection_rule: str
    matches: int
    steps: list[str]
    saved: SaveResult


def catalogue() -> list[Book]:
    try:
        return [Book.model_validate(row) for row in json.loads(
            (ROOT / "catalog.json").read_text(encoding="utf-8"))]
    except (OSError, ValueError) as exc:
        raise LibraryError("CATALOG_UNAVAILABLE: The local catalogue could not be loaded.") from exc


def search_catalog(query: str, limit: int = 5) -> SearchResult:
    """Read-only, all query words must occur in title, author, or subjects."""
    query = query.strip()
    if not query or len(query) > 120:
        raise LibraryError("INVALID_QUERY: Provide 1-120 non-whitespace characters.")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10:
        raise LibraryError("INVALID_LIMIT: limit must be an integer from 1 to 10.")
    terms = query.casefold().split()
    books = [b for b in catalogue() if all(
        term in f"{b.title} {b.author} {' '.join(b.subjects)}".casefold() for term in terms)]
    books.sort(key=lambda b: b.book_id)
    return SearchResult(query=query, count=len(books[:limit]), books=books[:limit])


def save_reading_item(book_id: str, list_name: str = "course") -> SaveResult:
    """Persist exactly one known book. Repeating the same pair is idempotent."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", list_name):
        raise LibraryError("INVALID_LIST: Use 1-32 letters, digits, underscores, or hyphens.")
    book = next((b for b in catalogue() if b.book_id == book_id), None)
    if book is None:
        raise LibraryError(f"UNKNOWN_BOOK: {book_id!r} is not in the catalogue; search first.")
    db = Path(os.environ.get("LIBRARY_DB", str(ROOT / "runtime" / "reading_list.sqlite3")))
    try:
        db.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db, timeout=5) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS reading_items (
                list_name TEXT NOT NULL, book_id TEXT NOT NULL, saved_at TEXT NOT NULL,
                PRIMARY KEY (list_name, book_id))""")
            stamp = datetime.now(timezone.utc).isoformat()
            cursor = conn.execute("INSERT OR IGNORE INTO reading_items VALUES (?, ?, ?)",
                                  (list_name, book_id, stamp))
            created = cursor.rowcount == 1
            saved_at = conn.execute(
                "SELECT saved_at FROM reading_items WHERE list_name=? AND book_id=?",
                (list_name, book_id)).fetchone()[0]
    except (OSError, sqlite3.Error) as exc:
        raise LibraryError("STORAGE_UNAVAILABLE: Could not save the reading item; retry later.") from exc
    return SaveResult(status="saved" if created else "already_saved", list_name=list_name,
                      book=book, saved_at=saved_at)


def plan_reading(query: str, list_name: str = "course") -> PlanResult:
    """Coordinate the same search and save functions used by the other two tools."""
    found = search_catalog(query, limit=10)
    if not found.books:
        raise LibraryError("NO_MATCH: No book matched; try fewer words. Nothing was saved.")
    saved = save_reading_item(found.books[0].book_id, list_name)
    return PlanResult(query=found.query, selection_rule="Lowest book_id among all matches",
                      matches=found.count,
                      steps=["search_catalog", "save_reading_item"], saved=saved)
