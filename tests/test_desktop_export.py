from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from numericosas.ingest.desktop_export import build_permalink, iter_chats


def write_export(
    root: Path,
    messages: list[dict],
    *,
    name: str = "Ana Gómez",
    chat_id: int = -1001234567890,
    username: str | None = None,
    chat_type: str = "private_channel",
) -> Path:
    folder = root / name.replace(" ", "_")
    folder.mkdir(parents=True, exist_ok=True)
    data = {
        "name": name,
        "type": chat_type,
        "id": chat_id,
        "username": username,
        "messages": messages,
    }
    (folder / "result.json").write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )
    return root


def test_flatten_text_and_links(tmp_path: Path) -> None:
    raw = write_export(
        tmp_path / "raw",
        [
            {
                "id": 1,
                "date": "2026-08-10T10:00:00-03:00",
                "text": [
                    "Mira ",
                    {"type": "text_link", "text": "esto", "href": "https://github.com/x/y"},
                    " y https://example.com/a.",
                ],
            }
        ],
    )
    chat = next(iter_chats(raw))
    message = chat.messages[0]

    assert message.text == "Mira esto y https://example.com/a."
    assert message.links == ["https://github.com/x/y", "https://example.com/a"]


def test_photo_reactions_and_service(tmp_path: Path) -> None:
    raw = write_export(
        tmp_path / "raw",
        [
            {
                "id": 1,
                "date": "2026-08-10T10:00:00-03:00",
                "text": "",
                "media_type": "photo",
                "photo": "photos/photo_1.jpg",
                "reactions": [
                    {"emoji": "👍", "count": 3},
                    {"emoji": "🔥", "count": 2},
                ],
                "views": 12,
            },
            {
                "id": 2,
                "type": "service",
                "date": "2026-08-10T11:00:00-03:00",
                "text": "",
            },
        ],
    )
    chat = next(iter_chats(raw))
    photo, service = chat.messages

    assert photo.media_type == "photo"
    assert photo.file_name == "photo_1.jpg"
    assert photo.reactions_total == 5
    assert photo.views == 12
    assert service.is_service is True


def test_permalink() -> None:
    assert build_permalink("-1001234567890", None, 7) == "https://t.me/c/1234567890/7"
    assert build_permalink("-1001234567890", "ana", 7) == "https://t.me/ana/7"
    assert build_permalink("123", None, 7) is None


def test_multiple_chats_in_one_export(tmp_path: Path) -> None:
    raw = write_export(
        tmp_path / "raw",
        [{"id": 1, "date": "2026-08-10T10:00:00-03:00", "text": "hola"}],
        name="Ana",
    )
    write_export(
        raw,
        [{"id": 1, "date": "2026-08-11T10:00:00-03:00", "text": "hola"}],
        name="Bruno",
        chat_id=-1001234567891,
    )
    chats = list(iter_chats(raw))
    assert {chat.title for chat in chats} == {"Ana", "Bruno"}


def test_missing_messages_are_ignored(tmp_path: Path) -> None:
    raw = write_export(
        tmp_path / "raw",
        [
            {"id": 1, "date": "2026-08-10T10:00:00-03:00", "text": "ok"},
            {"id": 2, "text": "sin fecha"},
        ],
    )
    chat = next(iter_chats(raw))
    assert [message.tg_message_id for message in chat.messages] == [1]


def test_naive_date_uses_unixtime_or_local_tz(tmp_path: Path) -> None:
    expected = datetime(2026, 8, 11, 2, 30, tzinfo=timezone.utc)
    raw = write_export(
        tmp_path / "raw",
        [
            {
                "id": 1,
                "date": "2026-08-10T23:30:00",
                "date_unixtime": str(int(expected.timestamp())),
                "text": "con unixtime",
            },
            {
                "id": 2,
                "date": "2026-08-10T23:30:00",
                "text": "sin unixtime",
            },
        ],
    )
    chat = next(
        iter_chats(raw, naive_tz=timezone(timedelta(hours=-3)))
    )
    assert chat.messages[0].date_utc == expected
    assert chat.messages[1].date_utc == expected


def test_chats_list_with_peer_ids(tmp_path: Path) -> None:
    folder = tmp_path / "raw" / "export"
    folder.mkdir(parents=True)
    data = {
        "chats": {
            "list": [
                {"id": 111, "name": "Ana", "type": "private_channel"},
                {"id": 222, "name": "Bruno", "type": "private_channel"},
            ]
        },
        "messages": [
            {
                "id": 1,
                "peer_id": 111,
                "date": "2026-08-10T10:00:00-03:00",
                "text": "de Ana",
            },
            {
                "id": 1,
                "peer_id": 222,
                "date": "2026-08-10T11:00:00-03:00",
                "text": "de Bruno",
            },
        ],
    }
    (folder / "result.json").write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )

    chats = {chat.title: chat for chat in iter_chats(tmp_path / "raw")}
    assert chats["Ana"].messages[0].text == "de Ana"
    assert chats["Bruno"].messages[0].text == "de Bruno"
