from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from numericosas import db
from numericosas.ingest.service import ingest_export
from numericosas.report.inventory import build_inventory
from numericosas.sample import generate_sample_export
from tests.test_desktop_export import write_export


def test_ingest_is_idempotent_and_normalizes_dates(tmp_path: Path) -> None:
    raw = write_export(
        tmp_path / "raw",
        [
            {
                "id": 1,
                "date": "2026-08-10T23:30:00+00:00",
                "text": "hola https://github.com/x/y",
            },
            {
                "id": 2,
                "date": "2026-08-11T01:00:00+00:00",
                "text": "",
                "media_type": "document",
                "file": "files/apunte.pdf",
                "file_name": "apunte.pdf",
            },
            {
                "id": 3,
                "type": "service",
                "date": "2026-08-11T02:00:00+00:00",
                "text": "",
            },
        ],
        username="ana",
    )
    db_path = tmp_path / "test.sqlite"

    first = ingest_export(raw, db_path, verbose=False)
    second = ingest_export(raw, db_path, verbose=False)

    assert first.messages_inserted == 2
    assert first.service_skipped == 1
    assert second.messages_inserted == 0
    assert second.messages_updated == 2

    conn = db.connect(db_path)
    rows = conn.execute("SELECT * FROM messages ORDER BY tg_message_id").fetchall()
    conn.close()
    assert len(rows) == 2
    assert rows[0]["date_local"].startswith("2026-08-10 20:30")
    assert rows[0]["iso_week"] == "2026-W33"
    assert rows[0]["permalink"] == "https://t.me/ana/1"
    assert rows[0]["link_domains_json"] == '["github.com"]'
    assert rows[1]["file_name"] == "apunte.pdf"


def test_sample_export_and_report(tmp_path: Path) -> None:
    raw = generate_sample_export(tmp_path / "raw")
    db_path = tmp_path / "demo.sqlite"
    out = tmp_path / "demo.xlsx"

    stats = ingest_export(raw, db_path, verbose=False)
    assert stats.chats_seen == 4
    assert stats.messages_inserted > 80
    assert stats.service_skipped == 4

    build_inventory(db_path, out)
    wb = load_workbook(out)
    assert wb.sheetnames == [
        "00_Portada",
        "01_Alumnos",
        "02_Inventario",
        "03_Resumen",
        "04_Timeline_Semanas",
        "05_Timeline_Meses",
        "06_Importacion",
        "99_Leyenda",
    ]
    assert wb["01_Alumnos"].max_row == 5
    assert wb["02_Inventario"].max_row == stats.messages_inserted + 1
    assert wb["03_Resumen"].max_row == 6
    assert wb["04_Timeline_Semanas"].max_column > 2
    assert wb["06_Importacion"].max_row == 2


def test_formula_text_is_written_as_text(tmp_path: Path) -> None:
    raw = write_export(
        tmp_path / "raw",
        [{"id": 1, "date": "2026-08-10T10:00:00-03:00", "text": "=1+1"}],
    )
    db_path = tmp_path / "test.sqlite"
    out = tmp_path / "test.xlsx"
    ingest_export(raw, db_path, verbose=False)
    build_inventory(db_path, out)

    wb = load_workbook(out)
    cell = wb["02_Inventario"].cell(row=2, column=23)
    assert cell.value == "=1+1"
    assert cell.data_type == "s"
