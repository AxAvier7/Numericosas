from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    display_name TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY,
    tg_chat_id TEXT UNIQUE,
    title TEXT NOT NULL,
    username TEXT,
    chat_type TEXT,
    source_folder TEXT,
    student_id INTEGER REFERENCES students(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    tg_message_id INTEGER NOT NULL,
    author TEXT,
    date_utc TEXT NOT NULL,
    date_local TEXT NOT NULL,
    iso_week TEXT NOT NULL,
    month TEXT NOT NULL,
    text TEXT NOT NULL DEFAULT '',
    text_len INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    media_type TEXT,
    file_name TEXT,
    file_path TEXT,
    mime_type TEXT,
    file_size INTEGER,
    links_json TEXT NOT NULL DEFAULT '[]',
    link_domains_json TEXT NOT NULL DEFAULT '[]',
    has_link INTEGER NOT NULL DEFAULT 0,
    reply_to_message_id INTEGER,
    reactions_total INTEGER NOT NULL DEFAULT 0,
    views INTEGER,
    forwarded_from TEXT,
    permalink TEXT,
    source_file TEXT,
    imported_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(channel_id, tg_message_id)
);

CREATE INDEX IF NOT EXISTS idx_messages_channel_date
    ON messages(channel_id, date_utc);
CREATE INDEX IF NOT EXISTS idx_messages_week
    ON messages(iso_week);

-- Fase M1: taxonomía editable y etiquetado manual.
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    dimension TEXT NOT NULL,
    description TEXT,
    color TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS labels (
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (message_id, tag_id)
);

CREATE TABLE IF NOT EXISTS import_runs (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    raw_dir TEXT,
    chats_seen INTEGER NOT NULL DEFAULT 0,
    messages_seen INTEGER NOT NULL DEFAULT 0,
    messages_inserted INTEGER NOT NULL DEFAULT 0,
    messages_updated INTEGER NOT NULL DEFAULT 0,
    service_skipped INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def upsert_channel(
    conn: sqlite3.Connection,
    *,
    title: str,
    tg_chat_id: str,
    username: str | None,
    chat_type: str | None,
    source_folder: str,
) -> tuple[int, int]:
    """Devuelve (channel_id, student_id). Crea el alumno si el canal es nuevo."""
    row = conn.execute(
        "SELECT id, student_id FROM channels WHERE tg_chat_id = ?",
        (tg_chat_id,),
    ).fetchone()

    if row is not None:
        channel_id = int(row["id"])
        student_id = row["student_id"]
        conn.execute(
            """
            UPDATE channels
               SET title = ?,
                   username = COALESCE(?, username),
                   chat_type = COALESCE(?, chat_type),
                   source_folder = ?
             WHERE id = ?
            """,
            (title, username, chat_type, source_folder, channel_id),
        )
        if student_id is None:
            student_id = _create_student(conn, title)
            conn.execute(
                "UPDATE channels SET student_id = ? WHERE id = ?",
                (student_id, channel_id),
            )
        return channel_id, int(student_id)

    student_id = _create_student(conn, title)
    cur = conn.execute(
        """
        INSERT INTO channels (tg_chat_id, title, username, chat_type, source_folder, student_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (tg_chat_id, title, username, chat_type, source_folder, student_id),
    )
    return int(cur.lastrowid), int(student_id)


def _create_student(conn: sqlite3.Connection, display_name: str) -> int:
    cur = conn.execute(
        "INSERT INTO students (display_name) VALUES (?)",
        (display_name,),
    )
    return int(cur.lastrowid)


def existing_message_ids(conn: sqlite3.Connection, channel_id: int) -> set[int]:
    rows = conn.execute(
        "SELECT tg_message_id FROM messages WHERE channel_id = ?",
        (channel_id,),
    )
    return {int(row["tg_message_id"]) for row in rows}


MESSAGE_FIELDS = (
    "channel_id",
    "tg_message_id",
    "author",
    "date_utc",
    "date_local",
    "iso_week",
    "month",
    "text",
    "text_len",
    "word_count",
    "media_type",
    "file_name",
    "file_path",
    "mime_type",
    "file_size",
    "links_json",
    "link_domains_json",
    "has_link",
    "reply_to_message_id",
    "reactions_total",
    "views",
    "forwarded_from",
    "permalink",
    "source_file",
)


def save_message(conn: sqlite3.Connection, values: dict, *, update: bool) -> None:
    if update:
        assignments = ", ".join(f"{field} = :{field}" for field in MESSAGE_FIELDS)
        conn.execute(
            f"""
            UPDATE messages
               SET {assignments}, imported_at = datetime('now')
             WHERE channel_id = :channel_id
               AND tg_message_id = :tg_message_id
            """,
            values,
        )
        return

    columns = ", ".join(MESSAGE_FIELDS)
    placeholders = ", ".join(f":{field}" for field in MESSAGE_FIELDS)
    conn.execute(
        f"INSERT INTO messages ({columns}) VALUES ({placeholders})",
        values,
    )
