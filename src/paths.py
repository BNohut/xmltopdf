"""Kaynak koddan calisirken ve PyInstaller ile paketlendikten sonra
resources/ klasorunu dogru bulan yardimci fonksiyon."""

from __future__ import annotations

import sys
from pathlib import Path


def resources_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "resources"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent / "resources"
