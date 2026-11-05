from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from numericosas import db
from numericosas.textutil import clean_text, truncate

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)
TITLE_FONT = Font(size=20, bold=True, color="1F3864")
SUBTITLE_FONT = Font(size=11, color="595959")
BOLD_FONT = Font(bold=True)
THIN = Side(style="thin", color="D9E2F3")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
TOP = Alignment(vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def build_inventory(db_path: str | Path, out_path: str | Path) -> Path:
    db_path = Path(db_path)
    out_path = Path(out_path)
    if not db_path.exists():
        raise FileNotFoundError(f"No existe la base: {db_path}")

    conn = db.connect(db_path)
    channels = conn.execute(
        """
        SELECT c.id AS channel_id,
               c.title AS channel_title,
               c.tg_chat_id,
               c.username,
               c.chat_type,
               s.id AS student_id,
               s.display_name AS student_name
          FROM channels c
          JOIN students s ON s.id = c.student_id
         ORDER BY s.display_name COLLATE NOCASE, c.title COLLATE NOCASE
        """
    ).fetchall()
    messages = conn.execute(
        """
        SELECT m.*,
               c.title AS channel_title,
               s.id AS student_id,
               s.display_name AS student_name
          FROM messages m
          JOIN channels c ON c.id = m.channel_id
          JOIN students s ON s.id = c.student_id
         ORDER BY s.display_name COLLATE NOCASE, m.date_utc
        """
    ).fetchall()
    runs = conn.execute("SELECT * FROM import_runs ORDER BY id").fetchall()
    conn.close()

    wb = Workbook()
    wb.remove(wb.active)

    _portada(wb.create_sheet("00_Portada"), channels, messages)
    _alumnos(wb.create_sheet("01_Alumnos"), channels, messages)
    _inventario(wb.create_sheet("02_Inventario"), messages)
    _resumen(wb.create_sheet("03_Resumen"), messages)
    _timeline(wb.create_sheet("04_Timeline_Semanas"), messages, "iso_week", "Semana ISO")
    _timeline(wb.create_sheet("05_Timeline_Meses"), messages, "month", "Mes")
    _importacion(wb.create_sheet("06_Importacion"), runs)
    _leyenda(wb.create_sheet("99_Leyenda"))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


def _portada(ws: Worksheet, channels, messages) -> None:
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = "1F3864"
    ws.merge_cells("A1:F1")
    ws["A1"] = "Numericosas — Inventario de actividad"
    ws["A1"].font = TITLE_FONT
    ws.row_dimensions[1].height = 32

    ws.merge_cells("A2:F2")
    ws["A2"] = "Fase M0: qué hay en los canales, antes de etiquetar."
    ws["A2"].font = SUBTITLE_FONT

    dates = sorted(m["date_local"] for m in messages)
    metadata = [
        ("Generado", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("Canales", str(len(channels))),
        ("Mensajes", str(len(messages))),
        ("Rango", f"{dates[0]}  →  {dates[-1]}" if dates else "sin mensajes"),
    ]
    row = 4
    for label, value in metadata:
        ws.cell(row=row, column=1, value=label).font = BOLD_FONT
        ws.cell(row=row, column=2, value=value)
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="Hojas").font = BOLD_FONT
    row += 1
    sheets = [
        ("01_Alumnos", "Una fila por canal/alumno: totales, actividad y rango de fechas."),
        ("02_Inventario", "Una fila por mensaje, con evidencia y link a Telegram."),
        ("03_Resumen", "Conteos por tipo de contenido y por alumno."),
        ("04_Timeline_Semanas", "Actividad por semana ISO: el recorrido en el tiempo."),
        ("05_Timeline_Meses", "La misma actividad agregada por mes."),
        ("06_Importacion", "Trazabilidad de cada corrida del importador."),
        ("99_Leyenda", "Definiciones y criterios de conteo."),
    ]
    for name, description in sheets:
        ws.cell(row=row, column=1, value=name)
        ws.cell(row=row, column=2, value=description)
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="Siguiente fase").font = BOLD_FONT
    ws.cell(
        row=row,
        column=2,
        value=(
            "M1: taxonomía editable y etiquetado manual. "
            "M2: tabla estudiantes × actividades y radares por dimensión."
        ),
    )
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 95
    ws.column_dimensions["C"].width = 20


def _alumnos(ws: Worksheet, channels, messages) -> None:
    ws.sheet_properties.tabColor = "2E75B6"
    headers = [
        "Alumno",
        "Canal",
        "Chat ID",
        "Usuario",
        "Tipo de chat",
        "Primer mensaje",
        "Último mensaje",
        "Total",
        "Días activos",
        "Semanas activas",
        "Con link",
        "Con media",
        "Respuestas",
        "Reacciones",
        "Caracteres",
        "Promedio/semana",
    ]
    _header(ws, headers)
    by_channel = defaultdict(list)
    for message in messages:
        by_channel[message["channel_id"]].append(message)

    for row_index, channel in enumerate(channels, start=2):
        items = by_channel.get(channel["channel_id"], [])
        days = {item["date_local"][:10] for item in items}
        weeks = {item["iso_week"] for item in items}
        values = [
            channel["student_name"],
            channel["channel_title"],
            channel["tg_chat_id"] or "",
            channel["username"] or "",
            channel["chat_type"] or "",
            items[0]["date_local"] if items else "",
            items[-1]["date_local"] if items else "",
            len(items),
            len(days),
            len(weeks),
            sum(1 for item in items if item["has_link"]),
            sum(1 for item in items if item["media_type"]),
            sum(1 for item in items if item["reply_to_message_id"]),
            sum(item["reactions_total"] or 0 for item in items),
            sum(item["text_len"] or 0 for item in items),
            round(len(items) / len(weeks), 1) if weeks else 0,
        ]
        _row(ws, row_index, values)

    last = max(len(channels) + 1, 2)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:P{last}"
    _widths(ws, [26, 30, 18, 18, 16, 18, 18, 9, 11, 13, 10, 11, 11, 11, 12, 14])
    ws.conditional_formatting.add(
        f"H2:H{last}",
        DataBarRule(start_type="num", start_value=0, end_type="max", color="2E75B6"),
    )


def _inventario(ws: Worksheet, messages) -> None:
    ws.sheet_properties.tabColor = "548235"
    headers = [
        "Alumno",
        "Canal",
        "Fecha local",
        "Semana ISO",
        "Mes",
        "ID",
        "Tipo",
        "Media export",
        "Archivo",
        "MIME",
        "KB",
        "Links",
        "Dominios",
        "Caracteres",
        "Palabras",
        "Respuesta",
        "Responde a",
        "Reacciones",
        "Vistas",
        "Reenviado de",
        "Permalink",
        "Fuente",
        "Texto",
    ]
    _header(ws, headers)

    for row_index, message in enumerate(messages, start=2):
        links = json.loads(message["links_json"] or "[]")
        domains = json.loads(message["link_domains_json"] or "[]")
        values = [
            message["student_name"],
            message["channel_title"],
            message["date_local"],
            message["iso_week"],
            message["month"],
            message["tg_message_id"],
            _media_bucket(message["media_type"], message["text"]),
            message["media_type"] or "",
            message["file_name"] or "",
            message["mime_type"] or "",
            round((message["file_size"] or 0) / 1024, 1) if message["file_size"] else "",
            "\n".join(links),
            ", ".join(domains),
            message["text_len"] or 0,
            message["word_count"] or 0,
            "Sí" if message["reply_to_message_id"] else "",
            message["reply_to_message_id"] or "",
            message["reactions_total"] or 0,
            message["views"] if message["views"] is not None else "",
            message["forwarded_from"] or "",
            message["permalink"] or "",
            f"{message['source_file']}#{message['tg_message_id']}",
            truncate(clean_text(message["text"]), 500),
        ]
        _row(ws, row_index, values)

        link_cell = ws.cell(row=row_index, column=21)
        if message["permalink"]:
            link_cell.hyperlink = message["permalink"]
            link_cell.font = Font(color="0563C1", underline="single")

    last = max(len(messages) + 1, 2)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:W{last}"
    _widths(
        ws,
        [
            22,
            26,
            17,
            12,
            9,
            8,
            12,
            14,
            26,
            16,
            9,
            34,
            22,
            10,
            10,
            10,
            10,
            10,
            9,
            18,
            30,
            30,
            70,
        ],
    )


def _resumen(ws: Worksheet, messages) -> None:
    ws.sheet_properties.tabColor = "BF8F00"
    headers = [
        "Alumno",
        "Total",
        "Texto",
        "Foto",
        "Documento",
        "Video",
        "Audio",
        "Sticker",
        "Otro",
        "Con link",
        "Respuestas",
    ]
    _header(ws, headers)
    by_student = defaultdict(list)
    for message in messages:
        by_student[(message["student_id"], message["student_name"])].append(message)

    rows = []
    for (_, name), items in sorted(by_student.items(), key=lambda pair: pair[0][1].lower()):
        buckets = defaultdict(int)
        for item in items:
            buckets[_media_bucket(item["media_type"], item["text"])] += 1
        rows.append(
            [
                name,
                len(items),
                buckets["Texto"],
                buckets["Foto"],
                buckets["Documento"],
                buckets["Video"],
                buckets["Audio"],
                buckets["Sticker"],
                buckets["Otro"],
                sum(1 for item in items if item["has_link"]),
                sum(1 for item in items if item["reply_to_message_id"]),
            ]
        )

    for row_index, values in enumerate(rows, start=2):
        _row(ws, row_index, values)

    total_row = len(rows) + 2
    totals = ["TOTAL"] + [
        sum(row[column] for row in rows) if rows else 0 for column in range(1, len(headers))
    ]
    _row(ws, total_row, totals, bold=True)
    for column in range(1, len(headers) + 1):
        ws.cell(row=total_row, column=column).fill = PatternFill("solid", fgColor="D9E2F3")

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:K{max(total_row, 2)}"
    _widths(ws, [26, 9, 9, 9, 12, 9, 9, 9, 9, 11, 11])
    if rows:
        ws.conditional_formatting.add(
            f"B2:K{total_row - 1}",
            ColorScaleRule(
                start_type="min",
                start_color="FFFFFF",
                end_type="max",
                end_color="9DC3E6",
            ),
        )


def _timeline(ws: Worksheet, messages, field: str, label: str) -> None:
    ws.sheet_properties.tabColor = "7030A0"
    labels = sorted({message[field] for message in messages})
    headers = ["Alumno", *labels, "Total"]
    _header(ws, headers)

    by_student = defaultdict(lambda: defaultdict(int))
    names: dict[tuple[int, str], str] = {}
    for message in messages:
        key = (message["student_id"], message["student_name"])
        names[key] = message["student_name"]
        by_student[key][message[field]] += 1

    ordered = sorted(names.items(), key=lambda item: item[1].lower())
    for row_index, (key, name) in enumerate(ordered, start=2):
        counts = by_student[key]
        values = [name, *[counts.get(item, 0) for item in labels], sum(counts.values())]
        _row(ws, row_index, values)

    last_row = max(len(ordered) + 1, 2)
    last_col = get_column_letter(max(len(headers), 2))
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{last_col}{last_row}"
    widths = [26] + [11] * len(labels) + [9]
    _widths(ws, widths)
    if labels and ordered:
        ws.conditional_formatting.add(
            f"B2:{get_column_letter(len(headers) - 1)}{last_row}",
            ColorScaleRule(
                start_type="min",
                start_color="FFFFFF",
                end_type="max",
                end_color="A9D18E",
            ),
        )
    ws.cell(row=1, column=1).comment = None
    ws.sheet_view.zoomScale = 90


def _importacion(ws: Worksheet, runs) -> None:
    ws.sheet_properties.tabColor = "7F7F7F"
    headers = [
        "ID",
        "Inicio (UTC)",
        "Fin (UTC)",
        "Carpeta",
        "Canales",
        "Mensajes vistos",
        "Insertados",
        "Actualizados",
        "Servicio omitidos",
        "Errores",
        "Notas",
    ]
    _header(ws, headers)
    for row_index, run in enumerate(runs, start=2):
        values = [
            run["id"],
            run["started_at"],
            run["finished_at"] or "",
            run["raw_dir"] or "",
            run["chats_seen"],
            run["messages_seen"],
            run["messages_inserted"],
            run["messages_updated"],
            run["service_skipped"],
            run["errors"],
            run["notes"] or "",
        ]
        _row(ws, row_index, values)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:K{max(len(runs) + 1, 2)}"
    _widths(ws, [6, 22, 22, 34, 9, 16, 12, 13, 16, 9, 50])


def _leyenda(ws: Worksheet) -> None:
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = "A6A6A6"
    ws["A1"] = "Leyenda y criterios de conteo"
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:B1")
    ws.row_dimensions[1].height = 28

    definitions = [
        ("Fecha local", "Fecha del mensaje en UTC-3. Se puede cambiar con --tz-offset al importar."),
        ("Semana ISO", "Semana ISO-8601, por ejemplo 2026-W33. Sirve para ver constancia."),
        ("Mes", "Año-mes local, por ejemplo 2026-08."),
        ("Tipo", "Texto, Foto, Documento, Video, Audio, Sticker u Otro, derivado de media_type."),
        ("Con media", "Mensaje con foto, documento, video, audio o sticker."),
        ("Con link", "Mensaje con al menos una URL en el texto o en una entidad text_link."),
        ("Respuesta", "Mensaje que responde a otro (reply_to_message_id)."),
        ("Reacciones", "Suma de reacciones del mensaje, si el export las incluye."),
        ("Vistas", "Views del canal. Es audiencia, no participación del dueño del canal."),
        ("Servicio omitido", "Pins, ingresos y otros eventos. No se cuentan como mensajes."),
        ("Permalink", "Link a Telegram si el canal es público o canal/supergrupo privado; si no, Fuente#ID."),
        ("Evidencia", "Cada fila se puede rastrear con Fuente + ID. La columna Texto está recortada a 500 caracteres."),
        ("Alcance", "M0 es un inventario descriptivo. No es una evaluación formal ni una nota."),
        ("Siguiente fase", "M1: etiquetas editables. M2: tabla estudiantes × actividades y radares."),
    ]
    row = 3
    for label, description in definitions:
        ws.cell(row=row, column=1, value=label).font = BOLD_FONT
        ws.cell(row=row, column=1).alignment = TOP
        ws.cell(row=row, column=2, value=description).alignment = WRAP
        row += 1

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 100


def _media_bucket(media_type: str | None, text: str | None) -> str:
    if not media_type:
        return "Texto" if (text or "").strip() else "Otro"
    value = media_type.lower()
    if "photo" in value or "image" in value:
        return "Foto"
    if "video" in value:
        return "Video"
    if "voice" in value or "audio" in value:
        return "Audio"
    if "sticker" in value:
        return "Sticker"
    if "document" in value or "file" in value:
        return "Documento"
    return "Otro"


def _header(ws: Worksheet, headers: list[str]) -> None:
    for column, value in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=column, value=value)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER
        cell.border = BORDER
    ws.row_dimensions[1].height = 32


def _row(ws: Worksheet, row: int, values: list, *, bold: bool = False) -> None:
    for column, value in enumerate(values, start=1):
        cell = ws.cell(row=row, column=column)
        if isinstance(value, str):
            text = clean_text(value)
            cell.value = text
            if text.startswith("="):
                cell.data_type = "s"
            cell.alignment = TOP
        else:
            cell.value = value
            cell.alignment = TOP
        if bold:
            cell.font = BOLD_FONT


def _widths(ws: Worksheet, widths: list[float]) -> None:
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = width
