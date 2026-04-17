"""Utilidades varias."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "rappi_ops_dummy_data.xlsx"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
