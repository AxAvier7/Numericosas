from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, timezone
from pathlib import Path

DEFAULT_TZ_OFFSET = -3


@dataclass(frozen=True)
class Config:
    """Rutas y zona horaria por defecto del pipeline."""

    raw_dir: Path = Path("data/raw")
    db_path: Path = Path("data/numericosas.sqlite")
    out_path: Path = Path("out/inventario.xlsx")
    tz_offset_hours: int = DEFAULT_TZ_OFFSET

    @property
    def local_tz(self) -> timezone:
        return timezone(timedelta(hours=self.tz_offset_hours))
