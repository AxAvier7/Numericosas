from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from numericosas import db
from numericosas.ingest.desktop_export import build_permalink, iter_chats
from numericosas.textutil import word_count


@dataclass
class IngestStats:
    chats_seen: int = 0
    messages_seen: int = 0
    messages_inserted: int = 0
    messages_updated: int = 0
    service_skipped: int = 0
    errors: int = 0
    notes: list[str] = field(default_factory=list)


def ingest_export(
    raw_dir: str | Path,
    db_path: str | Path,
    *,
    tz_offset_hours: int = -3,
    verbose: bool = True,
) -> IngestStats:
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de export: {raw_dir}")

    conn = db.connect(db_path)
    db.init_db(conn)
    local_tz = timezone(timedelta(hours=tz_offset_hours))

    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO import_runs (started_at, raw_dir) VALUES (?, ?)",
        (started_at, str(raw_dir)),
    )
    run_id = int(cur.lastrowid)
    conn.commit()

    stats = IngestStats()
    try:
        for chat in iter_chats(raw_dir, naive_tz=local_tz):
            try:
                _ingest_chat(conn, chat, stats, local_tz, raw_dir)
                conn.commit()
                if verbose:
                    print(
                        f"  {chat.title}: {len(chat.messages)} mensajes vistos",
                        file=sys.stderr,
                    )
            except Exception as exc:  # un canal roto no debe frenar el resto
                conn.rollback()
                stats.errors += 1
                stats.notes.append(f"{chat.title}: {exc}")
                if verbose:
                    print(f"  ERROR en {chat.title}: {exc}", file=sys.stderr)
    finally:
        finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            """
            UPDATE import_runs
               SET finished_at = ?,
                   chats_seen = ?,
                   messages_seen = ?,
                   messages_inserted = ?,
                   messages_updated = ?,
                   service_skipped = ?,
                   errors = ?,
                   notes = ?
             WHERE id = ?
            """,
            (
                finished_at,
                stats.chats_seen,
                stats.messages_seen,
                stats.messages_inserted,
                stats.messages_updated,
                stats.service_skipped,
                stats.errors,
                "\n".join(stats.notes),
                run_id,
            ),
        )
        conn.commit()
        conn.close()

    if verbose:
        print(
            f"Listo: {stats.chats_seen} canales, "
            f"{stats.messages_inserted} nuevos, "
            f"{stats.messages_updated} actualizados, "
            f"{stats.service_skipped} de servicio omitidos, "
            f"{stats.errors} errores.",
            file=sys.stderr,
        )
    return stats


def _ingest_chat(
    conn,
    chat,
    stats: IngestStats,
    local_tz: timezone,
    raw_dir: Path,
) -> None:
    stats.chats_seen += 1
    tg_chat_id = chat.tg_chat_id or f"folder:{chat.source_folder.as_posix()}"
    channel_id, _student_id = db.upsert_channel(
        conn,
        title=chat.title,
        tg_chat_id=tg_chat_id,
        username=chat.username,
        chat_type=chat.chat_type,
        source_folder=chat.source_folder.as_posix(),
    )
    existing = db.existing_message_ids(conn, channel_id)
    source_file = _relative_source(chat.source_file, raw_dir)

    for message in chat.messages:
        stats.messages_seen += 1
        if message.is_service:
            stats.service_skipped += 1
            continue

        local_date = message.date_utc.astimezone(local_tz)
        iso = local_date.isocalendar()
        links = message.links
        domains = sorted(
            {
                (urlparse(link).hostname or "").lower().removeprefix("www.")
                for link in links
                if urlparse(link).hostname
            }
        )

        values = {
            "channel_id": channel_id,
            "tg_message_id": message.tg_message_id,
            "author": message.author,
            "date_utc": message.date_utc.isoformat(timespec="seconds"),
            "date_local": local_date.replace(tzinfo=None).isoformat(
                sep=" ", timespec="minutes"
            ),
            "iso_week": f"{iso.year}-W{iso.week:02d}",
            "month": f"{local_date.year}-{local_date.month:02d}",
            "text": message.text,
            "text_len": len(message.text),
            "word_count": word_count(message.text),
            "media_type": message.media_type,
            "file_name": message.file_name,
            "file_path": message.file_path,
            "mime_type": message.mime_type,
            "file_size": message.file_size,
            "links_json": json.dumps(links, ensure_ascii=False),
            "link_domains_json": json.dumps(domains, ensure_ascii=False),
            "has_link": 1 if links else 0,
            "reply_to_message_id": message.reply_to_message_id,
            "reactions_total": message.reactions_total,
            "views": message.views,
            "forwarded_from": message.forwarded_from,
            "permalink": build_permalink(
                tg_chat_id, chat.username, message.tg_message_id
            ),
            "source_file": source_file,
        }

        is_update = message.tg_message_id in existing
        db.save_message(conn, values, update=is_update)
        if is_update:
            stats.messages_updated += 1
        else:
            stats.messages_inserted += 1
            existing.add(message.tg_message_id)


def _relative_source(path: Path, raw_dir: Path) -> str:
    if raw_dir.is_file():
        return path.name
    try:
        return str(path.relative_to(raw_dir))
    except ValueError:
        return str(path)
