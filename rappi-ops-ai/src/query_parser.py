"""Parser de preguntas en lenguaje natural.

Estrategia:
- enfoque deterministico y explicable
- regex + matching de alias + memoria conversacional
- suficiente para preguntas de negocio repetibles sobre datos tabulares
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from rapidfuzz import fuzz

from src.metric_catalog import (
    METRIC_ALIAS_TO_CANONICAL,
    PROBLEMATIC_KEYWORDS,
    normalize_text,
    resolve_country,
)


INTENT_PATTERNS = {
    "ranking": [r"top\s*\d+", r"cuales son las \d+", r"mayor", r"menor", r"top zonas"],
    "comparison": [r"compara", r"comparar", r"vs", r"versus", r"wealthy", r"non wealthy"],
    "trend": [r"evolucion", r"evolución", r"ultimas?\s*\d+\s*semanas", r"tendencia", r"serie"],
    "aggregation": [r"promedio", r"average", r"por pais", r"por país", r"agregado"],
    "multivariable": [r"alto .* bajo", r"bajo .* alto", r"y bajo", r"y alto"],
    "inference": [r"que podria explicar", r"qué podria explicar", r"que podria estar explicando", r"drivers", r"crecen en ordenes", r"crecen en órdenes"],
    "problematic_zones": [r"zonas problematic", r"zonas con problemas", r"deterioradas"],
}


@dataclass
class ParsedQuery:
    intent: str
    metric: Optional[str] = None
    metric_secondary: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    zone: Optional[str] = None
    timeframe_weeks: Optional[int] = None
    top_n: Optional[int] = None
    group_by: Optional[str] = None
    comparison_target: Optional[str] = None
    filters: Optional[Dict[str, str]] = None
    original_question: str = ""

    def to_dict(self) -> Dict[str, object]:
        return self.__dict__.copy()


class QueryParser:
    """Parser principal.

    Mejora importante:
    - prioriza match exacto de ZONE por sobre CITY
    - evita falsos positivos de ciudades cuando ya encontro una zona valida
    """

    def __init__(self, countries: Iterable[str], cities: Iterable[str], zones: Iterable[str], metrics: Iterable[str]) -> None:
        self.countries = list(countries)
        self.cities = list(cities)
        self.zones = list(zones)
        self.metrics = list(metrics)

    def parse(self, question: str) -> ParsedQuery:
        normalized = normalize_text(question)
        intent = self._detect_intent(normalized)
        metric = self._extract_metric(normalized)
        metric_secondary = self._extract_secondary_metric(normalized, metric)
        country = self._extract_country(question)

        zone = self._extract_zone(question)
        city = self._extract_city(question, disable_fuzzy=bool(zone))

        timeframe_weeks = self._extract_timeframe_weeks(normalized)
        top_n = self._extract_top_n(normalized)
        group_by, comparison_target = self._extract_grouping(normalized)
        filters = self._extract_filters(normalized)

        return ParsedQuery(
            intent=intent,
            metric=metric,
            metric_secondary=metric_secondary,
            country=country,
            city=city,
            zone=zone,
            timeframe_weeks=timeframe_weeks,
            top_n=top_n,
            group_by=group_by,
            comparison_target=comparison_target,
            filters=filters,
            original_question=question,
        )

    def _detect_intent(self, normalized: str) -> str:
        if any(keyword in normalized for keyword in [normalize_text(x) for x in PROBLEMATIC_KEYWORDS]):
            return "problematic_zones"

        scores = {}
        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, normalized):
                    score += 1
            scores[intent] = score

        best_intent = max(scores, key=scores.get)
        if scores[best_intent] == 0:
            return "aggregation"
        return best_intent

    def _extract_metric(self, normalized: str) -> Optional[str]:
        for alias, canonical in METRIC_ALIAS_TO_CANONICAL.items():
            if alias in normalized:
                return canonical

        best_match = None
        best_score = 0
        for alias, canonical in METRIC_ALIAS_TO_CANONICAL.items():
            score = fuzz.partial_ratio(alias, normalized)
            if score > best_score and score >= 88:
                best_score = score
                best_match = canonical
        return best_match

    def _extract_secondary_metric(self, normalized: str, primary_metric: Optional[str]) -> Optional[str]:
        detected = []
        for alias, canonical in METRIC_ALIAS_TO_CANONICAL.items():
            if alias in normalized and canonical not in detected:
                detected.append(canonical)
        for candidate in detected:
            if candidate != primary_metric:
                return candidate
        return None

    def _extract_country(self, raw_question: str) -> Optional[str]:
        words = re.split(r"[,.;:!?\-\s]+", raw_question)
        for token in words:
            code = resolve_country(token)
            if code:
                return code

        normalized = normalize_text(raw_question)
        for possible_name in ["argentina", "brasil", "brazil", "chile", "colombia", "costa rica", "ecuador", "mexico", "méxico", "peru", "perú", "uruguay"]:
            if normalize_text(possible_name) in normalized:
                return resolve_country(possible_name)
        return None

    def _extract_zone(self, raw_question: str) -> Optional[str]:
        return self._extract_named_entity(raw_question, self.zones, fuzzy_threshold=92)

    def _extract_city(self, raw_question: str, disable_fuzzy: bool = False) -> Optional[str]:
        return self._extract_named_entity(
            raw_question,
            self.cities,
            fuzzy_threshold=96,
            allow_fuzzy=not disable_fuzzy,
        )

    def _extract_named_entity(
        self,
        raw_question: str,
        entities: Iterable[str],
        fuzzy_threshold: int = 90,
        allow_fuzzy: bool = True,
    ) -> Optional[str]:
        normalized_question = normalize_text(raw_question)
        normalized_entities = {normalize_text(entity): entity for entity in entities}

        exact_matches = []
        for normalized_entity, original_entity in normalized_entities.items():
            if normalized_entity and normalized_entity in normalized_question:
                exact_matches.append((len(normalized_entity), original_entity))

        if exact_matches:
            exact_matches.sort(reverse=True)
            return exact_matches[0][1]

        if not allow_fuzzy:
            return None

        best_match = None
        best_score = 0
        for entity in entities:
            score = fuzz.partial_ratio(normalize_text(entity), normalized_question)
            if score > best_score and score >= fuzzy_threshold:
                best_score = score
                best_match = entity
        return best_match

    def _extract_timeframe_weeks(self, normalized: str) -> Optional[int]:
        match = re.search(r"ultimas?\s*(\d+)\s*semanas", normalized)
        if match:
            return int(match.group(1))
        match = re.search(r"ultimas?\s*(\d+)\s*weeks", normalized)
        if match:
            return int(match.group(1))
        if "esta semana" in normalized or "current week" in normalized:
            return 1
        return None

    def _extract_top_n(self, normalized: str) -> Optional[int]:
        match = re.search(r"top\s*(\d+)", normalized)
        if match:
            return int(match.group(1))
        match = re.search(r"cuales son las\s*(\d+)", normalized)
        if match:
            return int(match.group(1))
        if "5 zonas" in normalized:
            return 5
        return None

    def _extract_grouping(self, normalized: str) -> tuple[Optional[str], Optional[str]]:
        if "wealthy" in normalized and "non wealthy" in normalized:
            return "ZONE_TYPE", "Wealthy vs Non Wealthy"
        if "por pais" in normalized or "por país" in normalized:
            return "COUNTRY", None
        if "por ciudad" in normalized:
            return "CITY", None
        return None, None

    def _extract_filters(self, normalized: str) -> Dict[str, str]:
        filters: Dict[str, str] = {}
        if "wealthy" in normalized and "non wealthy" not in normalized:
            filters["ZONE_TYPE"] = "Wealthy"
        elif "non wealthy" in normalized and "wealthy" not in normalized:
            filters["ZONE_TYPE"] = "Non Wealthy"
        return filters
