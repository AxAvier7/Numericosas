from __future__ import annotations

from numericosas.ingest.base import IngestAdapter, ParsedChat, ParsedMessage
from numericosas.ingest.desktop_export import iter_chats
from numericosas.ingest.service import IngestStats, ingest_export

__all__ = [
    "IngestAdapter",
    "IngestStats",
    "ParsedChat",
    "ParsedMessage",
    "ingest_export",
    "iter_chats",
]
