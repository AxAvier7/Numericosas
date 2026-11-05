from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator, Protocol


@dataclass
class ParsedMessage:
    tg_message_id: int
    date_utc: datetime
    author: str | None = None
    text: str = ""
    is_service: bool = False
    media_type: str | None = None
    file_name: str | None = None
    file_path: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    links: list[str] = field(default_factory=list)
    reply_to_message_id: int | None = None
    reactions_total: int = 0
    views: int | None = None
    forwarded_from: str | None = None


@dataclass
class ParsedChat:
    title: str
    tg_chat_id: str | None
    username: str | None
    chat_type: str | None
    source_file: Path
    source_folder: Path
    messages: list[ParsedMessage] = field(default_factory=list)


class IngestAdapter(Protocol):
    """Interfaz común para export de Desktop y, más adelante, Telethon."""

    def iter_chats(self) -> Iterator[ParsedChat]: ...
