from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from numericosas.ingest.base import ParsedChat, ParsedMessage
from numericosas.textutil import clean_text, clean_url, dedupe, extract_urls


def iter_result_files(raw_dir: str | Path) -> list[Path]:
    raw_dir = Path(raw_dir)
    if raw_dir.is_file():
        if raw_dir.suffix.lower() == ".json":
            return [raw_dir]
        raise FileNotFoundError(f"No es un JSON de export: {raw_dir}")
    if not raw_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de export: {raw_dir}")
    return sorted(path for path in raw_dir.rglob("result.json") if path.is_file())


def iter_chats(
    raw_dir: str | Path,
    *,
    naive_tz: timezone = timezone.utc,
) -> Iterator[ParsedChat]:
    """Recorre todos los result.json de un export de Telegram Desktop.

    ``naive_tz`` se usa solo si un mensaje no trae ``date_unixtime`` y su
    ``date`` viene sin offset. En ese caso se interpreta como hora local del
    exportador, no como UTC.
    """
    raw_dir = Path(raw_dir)
    for path in iter_result_files(raw_dir):
        data = json.loads(path.read_text(encoding="utf-8"))
        yield from _chats_from_data(data, path, raw_dir, naive_tz)


def _chats_from_data(
    data: Any,
    path: Path,
    raw_dir: Path,
    naive_tz: timezone,
) -> Iterator[ParsedChat]:
    if isinstance(data, list):
        for item in data:
            yield from _chats_from_data(item, path, raw_dir, naive_tz)
        return

    if not isinstance(data, dict):
        return

    chats = data.get("chats")
    if isinstance(chats, dict):
        chats = chats.get("list", [])
    top_messages = data.get("messages")

    # Formato con una lista de chats y mensajes sueltos identificados por peer_id.
    if isinstance(chats, list) and isinstance(top_messages, list) and any(
        isinstance(message, dict) and "peer_id" in message for message in top_messages
    ):
        by_peer: dict[str, list[dict]] = defaultdict(list)
        for message in top_messages:
            if isinstance(message, dict):
                by_peer[_peer_key(message.get("peer_id"))].append(message)
        for chat in chats:
            if not isinstance(chat, dict):
                continue
            messages = by_peer.get(_peer_key(chat.get("id", chat.get("chat_id"))), [])
            if messages:
                yield _parse_chat(
                    {**chat, "messages": messages}, path, raw_dir, naive_tz
                )
        return

    if isinstance(top_messages, list):
        yield _parse_chat(data, path, raw_dir, naive_tz)
        return

    if isinstance(chats, list):
        for chat in chats:
            if isinstance(chat, dict) and isinstance(chat.get("messages"), list):
                yield _parse_chat(chat, path, raw_dir, naive_tz)


def _peer_key(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("channel_id", "chat_id", "user_id"):
            if key in value:
                return str(value[key])
    return str(value)


def _parse_chat(
    data: dict,
    path: Path,
    raw_dir: Path,
    naive_tz: timezone,
) -> ParsedChat:
    title = _first_str(data.get("name"), data.get("title"), path.parent.name)
    chat_id = data.get("id", data.get("chat_id"))
    tg_chat_id = str(chat_id) if chat_id is not None else None
    username = _first_username(data)
    chat_type = data.get("type")

    source_folder = _relative_folder(path, raw_dir)
    messages: list[ParsedMessage] = []
    for raw in data.get("messages", []):
        if not isinstance(raw, dict):
            continue
        parsed = _parse_message(raw, path, raw_dir, naive_tz)
        if parsed is not None:
            messages.append(parsed)

    return ParsedChat(
        title=title,
        tg_chat_id=tg_chat_id,
        username=username,
        chat_type=chat_type,
        source_file=path,
        source_folder=Path(source_folder),
        messages=messages,
    )


def _parse_message(
    raw: dict,
    path: Path,
    raw_dir: Path,
    naive_tz: timezone,
) -> ParsedMessage | None:
    message_id = raw.get("id")
    if message_id is None:
        return None
    try:
        message_id = int(message_id)
    except (TypeError, ValueError):
        return None

    date = _parse_date(raw, naive_tz)
    if date is None:
        return None

    text, links = _flatten_text(raw.get("text"))
    links.extend(_webpage_links(raw))
    links = dedupe(clean_url(link) for link in links)

    media_type, file_rel, file_name = _media_info(raw)
    file_path = _relative_media_path(path, raw_dir, file_rel)

    return ParsedMessage(
        tg_message_id=message_id,
        date_utc=date,
        author=_opt_str(raw.get("from")),
        text=clean_text(text),
        is_service=raw.get("type") == "service",
        media_type=media_type,
        file_name=file_name,
        file_path=file_path,
        mime_type=_opt_str(raw.get("mime_type")),
        file_size=_opt_int(raw.get("file_size")),
        links=links,
        reply_to_message_id=_opt_int(raw.get("reply_to_message_id")),
        reactions_total=_sum_reactions(raw.get("reactions")),
        views=_opt_int(raw.get("views")),
        forwarded_from=_opt_str(raw.get("forwarded_from")),
    )


def _flatten_text(value: Any) -> tuple[str, list[str]]:
    parts: list[str] = []
    extra_links: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, dict):
            if item.get("type") == "text_link":
                href = item.get("href")
                if isinstance(href, str):
                    extra_links.append(href)
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
            elif isinstance(text, (list, dict)):
                walk(text)

    walk(value)
    text = "".join(parts)
    return text, dedupe([*extra_links, *extract_urls(text)])


def _webpage_links(raw: dict) -> list[str]:
    webpage = raw.get("webpage")
    if isinstance(webpage, dict):
        url = webpage.get("url")
        if isinstance(url, str):
            return [url]
    return []


def _media_info(raw: dict) -> tuple[str | None, str | None, str | None]:
    media_type = _opt_str(raw.get("media_type"))
    if media_type == "webpage":
        media_type = None

    file_rel = _opt_str(raw.get("photo")) or _opt_str(raw.get("file"))
    if file_rel and file_rel.startswith("("):
        # "(File not included...)" cuando el export no bajó el archivo.
        file_rel = None

    if media_type is None and file_rel:
        media_type = "photo" if raw.get("photo") else "document"

    file_name = _opt_str(raw.get("file_name"))
    if file_name is None and file_rel:
        file_name = Path(file_rel).name

    return media_type, file_rel, file_name


def _parse_date(raw: dict, naive_tz: timezone) -> datetime | None:
    # date_unixtime es inequívoco; date sin offset es hora local del exportador.
    unixtime = raw.get("date_unixtime")
    if unixtime not in (None, ""):
        try:
            return datetime.fromtimestamp(int(unixtime), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass

    value = raw.get("date")
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=naive_tz)
        return parsed.astimezone(timezone.utc)
    return None


def _sum_reactions(value: Any) -> int:
    if isinstance(value, list):
        return sum(_sum_reactions(item) for item in value)
    if isinstance(value, dict):
        if "results" in value:
            return _sum_reactions(value["results"])
        return _opt_int(value.get("count")) or 0
    return 0


def _first_username(data: dict) -> str | None:
    username = data.get("username")
    if isinstance(username, str) and username:
        return username
    usernames = data.get("usernames")
    if isinstance(usernames, list):
        active = [
            item.get("username")
            for item in usernames
            if isinstance(item, dict) and item.get("active") and item.get("username")
        ]
        if active:
            return str(active[0])
        for item in usernames:
            if isinstance(item, dict) and item.get("username"):
                return str(item["username"])
    return None


def _first_str(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "sin nombre"


def _opt_str(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _opt_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _relative_folder(path: Path, raw_dir: Path) -> Path:
    if raw_dir.is_file():
        return Path(path.parent.name)
    try:
        return path.parent.relative_to(raw_dir)
    except ValueError:
        return Path(path.parent.name)


def _relative_media_path(path: Path, raw_dir: Path, file_rel: str | None) -> str | None:
    if not file_rel:
        return None
    candidate = path.parent / file_rel
    if raw_dir.is_file():
        return str(candidate)
    try:
        return str(candidate.relative_to(raw_dir))
    except ValueError:
        return str(candidate)


def build_permalink(
    tg_chat_id: str | None,
    username: str | None,
    message_id: int,
) -> str | None:
    """Link público o t.me/c para canales/supergrupos privados."""
    if username:
        return f"https://t.me/{username}/{message_id}"
    if not tg_chat_id:
        return None
    try:
        numeric_id = int(tg_chat_id)
    except ValueError:
        return None
    if numeric_id >= 0:
        return None
    internal = str(abs(numeric_id))
    if internal.startswith("100"):
        internal = internal[3:]
    return f"https://t.me/c/{internal}/{message_id}"
