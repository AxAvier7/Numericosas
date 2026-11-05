from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from numericosas import __version__
from numericosas.ingest.service import ingest_export
from numericosas.report.inventory import build_inventory
from numericosas.sample import generate_sample_export


def main(argv: list[str] | None = None) -> int:
    _configure_console()
    parser = argparse.ArgumentParser(
        prog="numericosas",
        description="Inventario de actividad de canales de Telegram para Matemática Numérica.",
    )
    parser.add_argument("--version", action="version", version=f"numericosas {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser(
        "ingest",
        help="Importa un export de Telegram Desktop a SQLite.",
    )
    ingest.add_argument("--raw", type=Path, default=Path("data/raw"))
    ingest.add_argument("--db", type=Path, default=Path("data/numericosas.sqlite"))
    ingest.add_argument("--tz-offset", type=int, default=-3)

    report = subparsers.add_parser(
        "report",
        help="Genera el Excel de inventario.",
    )
    report.add_argument("--db", type=Path, default=Path("data/numericosas.sqlite"))
    report.add_argument("--out", type=Path, default=Path("out/inventario.xlsx"))

    demo = subparsers.add_parser(
        "demo",
        help="Genera datos sintéticos, importa y arma el Excel de ejemplo.",
    )
    demo.add_argument("--raw", type=Path, default=Path("data/raw/demo"))
    demo.add_argument("--db", type=Path, default=Path("data/demo.sqlite"))
    demo.add_argument("--out", type=Path, default=Path("out/demo_inventario.xlsx"))
    demo.add_argument("--tz-offset", type=int, default=-3)

    args = parser.parse_args(argv)

    try:
        if args.command == "ingest":
            stats = ingest_export(args.raw, args.db, tz_offset_hours=args.tz_offset)
            print(f"Base: {args.db}")
            print(
                f"Canales: {stats.chats_seen} | Mensajes: {stats.messages_seen} | "
                f"Nuevos: {stats.messages_inserted} | Actualizados: {stats.messages_updated} | "
                f"Servicio omitido: {stats.service_skipped} | Errores: {stats.errors}"
            )
            return 0

        if args.command == "report":
            out = build_inventory(args.db, args.out)
            print(f"Excel: {out}")
            return 0

        if args.command == "demo":
            _reset_demo(args.raw, args.db)
            generate_sample_export(args.raw)
            stats = ingest_export(args.raw, args.db, tz_offset_hours=args.tz_offset)
            out = build_inventory(args.db, args.out)
            print(f"Demo generada: {args.raw}")
            print(
                f"Canales: {stats.chats_seen} | Mensajes: {stats.messages_seen} | "
                f"Nuevos: {stats.messages_inserted} | Servicio omitido: {stats.service_skipped}"
            )
            print(f"Excel: {out}")
            return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


def _reset_demo(raw: Path, db_path: Path) -> None:
    if raw.exists():
        shutil.rmtree(raw)
    for suffix in ("", "-wal", "-shm"):
        Path(f"{db_path}{suffix}").unlink(missing_ok=True)


def _configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
