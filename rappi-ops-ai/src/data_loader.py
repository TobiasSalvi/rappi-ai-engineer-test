"""Carga y normalizacion del dataset.

Objetivo:
- leer el Excel original
- llevar las hojas a un formato largo comun
- facilitar filtros y calculos por semana
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import pandas as pd

ROLLING_WEEK_COLUMNS = [f"L{i}W_ROLL" for i in range(8, -1, -1)]
ORDERS_WEEK_COLUMNS = [f"L{i}W" for i in range(8, -1, -1)]


@dataclass
class DataBundle:
    """Contenedor tipado con los dataframes principales."""

    metrics_wide: pd.DataFrame
    orders_wide: pd.DataFrame
    metrics_long: pd.DataFrame
    orders_long: pd.DataFrame
    unified_long: pd.DataFrame


def _melt_metrics(df: pd.DataFrame) -> pd.DataFrame:
    long_df = df.melt(
        id_vars=[
            "COUNTRY",
            "CITY",
            "ZONE",
            "ZONE_TYPE",
            "ZONE_PRIORITIZATION",
            "METRIC",
        ],
        value_vars=ROLLING_WEEK_COLUMNS,
        var_name="week_label",
        value_name="value",
    )
    long_df["week_index"] = long_df["week_label"].str.extract(r"L(\d+)W").astype(int)
    long_df["is_current_week"] = long_df["week_index"] == 0
    return long_df



def _melt_orders(df: pd.DataFrame) -> pd.DataFrame:
    long_df = df.melt(
        id_vars=["COUNTRY", "CITY", "ZONE", "METRIC"],
        value_vars=ORDERS_WEEK_COLUMNS,
        var_name="week_label",
        value_name="value",
    )
    long_df["week_index"] = long_df["week_label"].str.extract(r"L(\d+)W").astype(int)
    long_df["is_current_week"] = long_df["week_index"] == 0
    long_df["ZONE_TYPE"] = "Unknown"
    long_df["ZONE_PRIORITIZATION"] = "Unknown"
    return long_df



def load_data(excel_path: str | Path) -> DataBundle:
    """Lee el Excel y devuelve dataframes listos para consumo.

    Parameters
    ----------
    excel_path:
        Ruta al archivo xlsx.
    """
    excel_path = Path(excel_path)
    metrics_wide = pd.read_excel(excel_path, sheet_name="RAW_INPUT_METRICS")
    orders_wide = pd.read_excel(excel_path, sheet_name="RAW_ORDERS")

    metrics_long = _melt_metrics(metrics_wide)
    orders_long = _melt_orders(orders_wide)

    # Unificamos columnas para que el motor analitico trabaje contra un solo esquema.
    unified_long = pd.concat([
        metrics_long,
        orders_long[
            [
                "COUNTRY",
                "CITY",
                "ZONE",
                "ZONE_TYPE",
                "ZONE_PRIORITIZATION",
                "METRIC",
                "week_label",
                "value",
                "week_index",
                "is_current_week",
            ]
        ],
    ], ignore_index=True)

    # Dejar week_index como entero y ordenar para analisis temporal.
    unified_long["week_index"] = unified_long["week_index"].astype(int)
    unified_long = unified_long.sort_values(
        by=["COUNTRY", "CITY", "ZONE", "METRIC", "week_index"],
        ascending=[True, True, True, True, False],
    ).reset_index(drop=True)

    return DataBundle(
        metrics_wide=metrics_wide,
        orders_wide=orders_wide,
        metrics_long=metrics_long,
        orders_long=orders_long,
        unified_long=unified_long,
    )



def get_available_entities(bundle: DataBundle) -> Tuple[list[str], list[str], list[str], list[str]]:
    """Devuelve entidades utiles para el parser y autocompletado."""
    countries = sorted(bundle.unified_long["COUNTRY"].dropna().unique().tolist())
    cities = sorted(bundle.unified_long["CITY"].dropna().unique().tolist())
    zones = sorted(bundle.unified_long["ZONE"].dropna().unique().tolist())
    metrics = sorted(bundle.unified_long["METRIC"].dropna().unique().tolist())
    return countries, cities, zones, metrics
