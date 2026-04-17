"""Catalogo de metricas, alias y metadata de negocio.

Este modulo centraliza todos los nombres de metricas y sus variaciones.
Asi evitamos que la app, el parser y el motor analitico se desincronicen.
"""

from __future__ import annotations

import unicodedata
from typing import Dict, List

# Mapeo de codigos de pais a nombres y viceversa.
COUNTRY_NAME_BY_CODE: Dict[str, str] = {
    "AR": "Argentina",
    "BR": "Brasil",
    "CL": "Chile",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "EC": "Ecuador",
    "MX": "Mexico",
    "PE": "Peru",
    "UY": "Uruguay",
}

COUNTRY_CODE_BY_NAME: Dict[str, str] = {
    "argentina": "AR",
    "brasil": "BR",
    "brazil": "BR",
    "chile": "CL",
    "colombia": "CO",
    "costa rica": "CR",
    "ecuador": "EC",
    "mexico": "MX",
    "méxico": "MX",
    "peru": "PE",
    "perú": "PE",
    "uruguay": "UY",
}

# Canonical metric definitions.
METRIC_METADATA: Dict[str, Dict[str, object]] = {
    "% PRO Users Who Breakeven": {
        "aliases": [
            "% pro users who breakeven",
            "pro breakeven",
            "breakeven pro",
        ],
        "higher_is_better": True,
        "family": "pro",
    },
    "% Restaurants Sessions With Optimal Assortment": {
        "aliases": [
            "% restaurants sessions with optimal assortment",
            "optimal assortment",
            "restaurant sessions optimal assortment",
        ],
        "higher_is_better": True,
        "family": "restaurant assortment",
    },
    "Gross Profit UE": {
        "aliases": [
            "gross profit ue",
            "gross profit",
            "gp ue",
            "ue gross profit",
        ],
        "higher_is_better": True,
        "family": "profitability",
    },
    "Lead Penetration": {
        "aliases": [
            "lead penetration",
            "lp",
        ],
        "higher_is_better": True,
        "family": "supply",
    },
    "MLTV Top Verticals Adoption": {
        "aliases": [
            "mltv top verticals adoption",
            "top verticals adoption",
            "mltv adoption",
        ],
        "higher_is_better": True,
        "family": "cross-sell",
    },
    "Non-Pro PTC > OP": {
        "aliases": [
            "non-pro ptc > op",
            "non pro ptc op",
            "ptc to op",
        ],
        "higher_is_better": True,
        "family": "conversion",
    },
    "Perfect Orders": {
        "aliases": [
            "perfect orders",
            "perfect order",
            "po",
        ],
        "higher_is_better": True,
        "family": "operations",
    },
    "Pro Adoption (Last Week Status)": {
        "aliases": [
            "pro adoption",
            "pro adoption (last week status)",
            "pro adoption last week status",
        ],
        "higher_is_better": True,
        "family": "pro",
    },
    "Restaurants Markdowns / GMV": {
        "aliases": [
            "restaurants markdowns / gmv",
            "markdowns gmv",
            "restaurant markdowns",
        ],
        "higher_is_better": False,
        "family": "discounts",
    },
    "Restaurants SS > ATC CVR": {
        "aliases": [
            "restaurants ss > atc cvr",
            "restaurant ss atc cvr",
            "ss to atc",
        ],
        "higher_is_better": True,
        "family": "conversion",
    },
    "Restaurants SST > SS CVR": {
        "aliases": [
            "restaurants sst > ss cvr",
            "restaurant sst ss cvr",
            "sst to ss restaurants",
        ],
        "higher_is_better": True,
        "family": "discovery",
    },
    "Retail SST > SS CVR": {
        "aliases": [
            "retail sst > ss cvr",
            "retail sst ss cvr",
            "sst to ss retail",
        ],
        "higher_is_better": True,
        "family": "discovery",
    },
    "Turbo Adoption": {
        "aliases": [
            "turbo adoption",
        ],
        "higher_is_better": True,
        "family": "turbo",
    },
    "Orders": {
        "aliases": [
            "orders",
            "ordenes",
            "órdenes",
            "pedidos",
        ],
        "higher_is_better": True,
        "family": "volume",
    },
}

PROBLEMATIC_KEYWORDS = [
    "problematicas",
    "problematicas",
    "problematic",
    "zonas problematicas",
    "zonas problemáticas",
    "zonas con problemas",
    "zonas deterioradas",
]


def normalize_text(value: str) -> str:
    """Normaliza texto para matching robusto.

    - baja a minusculas
    - remueve tildes
    - elimina espacios dobles
    """
    value = value or ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    return " ".join(value.split())


METRIC_ALIAS_TO_CANONICAL: Dict[str, str] = {}
for canonical_metric, meta in METRIC_METADATA.items():
    METRIC_ALIAS_TO_CANONICAL[normalize_text(canonical_metric)] = canonical_metric
    for alias in meta.get("aliases", []):
        METRIC_ALIAS_TO_CANONICAL[normalize_text(alias)] = canonical_metric


def get_metric_aliases() -> List[str]:
    """Devuelve todos los alias conocidos para el parser."""
    return list(METRIC_ALIAS_TO_CANONICAL.keys())


def resolve_country(value: str) -> str | None:
    """Resuelve un pais por codigo o nombre a su codigo canonico."""
    normalized = normalize_text(value)
    if not normalized:
        return None

    upper_value = value.strip().upper()
    if upper_value in COUNTRY_NAME_BY_CODE:
        return upper_value

    return COUNTRY_CODE_BY_NAME.get(normalized)


def country_display_name(country_code: str) -> str:
    """Devuelve el nombre amigable del pais."""
    return COUNTRY_NAME_BY_CODE.get(country_code, country_code)
