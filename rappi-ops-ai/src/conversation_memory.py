"""Memoria conversacional minima y util.

No intentamos replicar un chat generalista. Guardamos solo el contexto que
sirve para completar preguntas de seguimiento.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ConversationMemory:
    """Estado de la sesion conversacional."""

    country: Optional[str] = None
    city: Optional[str] = None
    zone: Optional[str] = None
    metric: Optional[str] = None
    comparison_target: Optional[str] = None
    timeframe_weeks: Optional[int] = None
    last_intent: Optional[str] = None
    extra_filters: Dict[str, Any] = field(default_factory=dict)

    def update_from_query(self, query: Dict[str, Any]) -> None:
        """Actualiza la memoria solo con valores presentes."""
        for field_name in ["country", "city", "zone", "metric", "timeframe_weeks", "last_intent"]:
            if query.get(field_name):
                setattr(self, field_name, query.get(field_name))

        if query.get("comparison_target"):
            self.comparison_target = query["comparison_target"]

        if query.get("filters"):
            self.extra_filters.update(query["filters"])

    def hydrate(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Completa una query parcial con el contexto previo."""
        hydrated = dict(query)
        hydrated.setdefault("country", self.country)
        hydrated.setdefault("city", self.city)
        hydrated.setdefault("zone", self.zone)
        hydrated.setdefault("metric", self.metric)
        hydrated.setdefault("timeframe_weeks", self.timeframe_weeks)
        return hydrated
