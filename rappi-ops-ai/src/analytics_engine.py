"""Motor analitico para responder preguntas de negocio.

Este modulo ejecuta la logica principal sobre pandas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd

from src.metric_catalog import METRIC_METADATA, country_display_name


@dataclass
class AnalysisResult:
    kind: str
    title: str
    dataframe: pd.DataFrame
    summary: str
    chart_type: Optional[str] = None
    metadata: Optional[Dict[str, object]] = None


class AnalyticsEngine:
    """Ejecuta analisis sobre el dataset unificado."""

    def __init__(self, unified_long: pd.DataFrame) -> None:
        self.df = unified_long.copy()

    def run(self, query: Dict[str, object]) -> AnalysisResult:
        intent = query.get("intent")
        if intent == "ranking":
            return self._run_ranking(query)
        if intent == "comparison":
            return self._run_comparison(query)
        if intent == "trend":
            return self._run_trend(query)
        if intent == "multivariable":
            return self._run_multivariable(query)
        if intent == "inference":
            return self._run_growth_inference(query)
        if intent == "problematic_zones":
            return self._run_problematic_zones(query)
        return self._run_aggregation(query)

    def _base_filter(self, query: Dict[str, object], metric_override: Optional[str] = None) -> pd.DataFrame:
        df = self.df.copy()
        metric = metric_override or query.get("metric")
        if metric:
            df = df[df["METRIC"] == metric]
        if query.get("country"):
            df = df[df["COUNTRY"] == query["country"]]
        if query.get("city"):
            df = df[df["CITY"] == query["city"]]
        if query.get("zone"):
            df = df[df["ZONE"] == query["zone"]]
        filters = query.get("filters") or {}
        for key, value in filters.items():
            if key in df.columns:
                df = df[df[key] == value]
        return df

    def _run_ranking(self, query: Dict[str, object]) -> AnalysisResult:
        df = self._base_filter(query)
        if df.empty:
            return self._empty_result("ranking", "No se encontraron datos para ese ranking.")

        current = df[df["week_index"] == 0]
        ascending = not METRIC_METADATA.get(query.get("metric"), {}).get("higher_is_better", True)
        top_n = int(query.get("top_n") or 5)

        grouped = (
            current.groupby(["COUNTRY", "CITY", "ZONE"], as_index=False)["value"]
            .mean()
            .sort_values("value", ascending=ascending)
            .head(top_n)
        )
        title = f"Top {top_n} zonas por {query.get('metric')}"
        country_phrase = country_display_name(query["country"]) if query.get("country") else "todos los paises"
        summary = f"Se muestran las {top_n} zonas destacadas en {query.get('metric')} para {country_phrase}, tomando la semana actual (L0W)."
        return AnalysisResult("ranking", title, grouped, summary, chart_type="bar")

    def _run_comparison(self, query: Dict[str, object]) -> AnalysisResult:
        df = self._base_filter(query)
        if df.empty:
            return self._empty_result("comparison", "No se encontraron datos para esa comparacion.")

        current = df[df["week_index"] == 0]
        group_by = query.get("group_by") or "ZONE_TYPE"
        grouped = current.groupby(group_by, as_index=False)["value"].mean().sort_values("value", ascending=False)
        title = f"Comparacion de {query.get('metric')} por {group_by}"
        summary = f"Comparacion promedio de {query.get('metric')} en la semana actual agrupada por {group_by}."
        return AnalysisResult("comparison", title, grouped, summary, chart_type="bar")

    def _run_trend(self, query: Dict[str, object]) -> AnalysisResult:
        df = self._base_filter(query)
        if df.empty:
            return self._empty_result("trend", "No se encontraron datos para esa tendencia.")

        timeframe = int(query.get("timeframe_weeks") or 8)
        # week_index 0 es actual; tomamos de 0 a timeframe-1.
        selected_weeks = list(range(0, min(timeframe, 9)))
        trend = (
            df[df["week_index"].isin(selected_weeks)]
            .groupby("week_index", as_index=False)["value"]
            .mean()
            .sort_values("week_index", ascending=False)
        )
        title = f"Evolucion de {query.get('metric')}"
        summary = f"Serie temporal de {query.get('metric')} para las ultimas {timeframe} semanas disponibles."
        return AnalysisResult("trend", title, trend, summary, chart_type="line")

    def _run_aggregation(self, query: Dict[str, object]) -> AnalysisResult:
        df = self._base_filter(query)
        if df.empty:
            return self._empty_result("aggregation", "No se encontraron datos para esa agregacion.")

        current = df[df["week_index"] == 0]
        group_by = query.get("group_by") or "COUNTRY"
        grouped = current.groupby(group_by, as_index=False)["value"].mean().sort_values("value", ascending=False)
        title = f"Promedio de {query.get('metric')} por {group_by}"
        summary = f"Promedio actual de {query.get('metric')} agrupado por {group_by}."
        return AnalysisResult("aggregation", title, grouped, summary, chart_type="bar")

    def _run_multivariable(self, query: Dict[str, object]) -> AnalysisResult:
        metric_x = query.get("metric") or "Lead Penetration"
        metric_y = query.get("metric_secondary") or "Perfect Orders"

        x_df = self._base_filter(query, metric_override=metric_x)
        y_df = self._base_filter(query, metric_override=metric_y)
        x_df = x_df[x_df["week_index"] == 0]
        y_df = y_df[y_df["week_index"] == 0]

        merged = pd.merge(
            x_df[["COUNTRY", "CITY", "ZONE", "value"]].rename(columns={"value": metric_x}),
            y_df[["COUNTRY", "CITY", "ZONE", "value"]].rename(columns={"value": metric_y}),
            on=["COUNTRY", "CITY", "ZONE"],
            how="inner",
        )
        if merged.empty:
            return self._empty_result("multivariable", "No se encontraron datos para ese cruce multivariable.")

        x_threshold = merged[metric_x].quantile(0.75)
        y_threshold = merged[metric_y].quantile(0.25)
        result = merged[(merged[metric_x] >= x_threshold) & (merged[metric_y] <= y_threshold)].sort_values(metric_x, ascending=False)
        title = f"Zonas con alto {metric_x} y bajo {metric_y}"
        summary = f"Se identifican zonas en el cuartil superior de {metric_x} y cuartil inferior de {metric_y}."
        return AnalysisResult("multivariable", title, result, summary, chart_type="scatter")

    def _run_growth_inference(self, query: Dict[str, object]) -> AnalysisResult:
        orders_df = self._base_filter(query, metric_override="Orders")
        if orders_df.empty:
            return self._empty_result("inference", "No se encontraron ordenes para analizar crecimiento.")

        timeframe = int(query.get("timeframe_weeks") or 5)
        selected_weeks = list(range(0, min(timeframe, 9)))
        recent = orders_df[orders_df["week_index"].isin(selected_weeks)].copy()
        pivot = recent.pivot_table(index=["COUNTRY", "CITY", "ZONE"], columns="week_index", values="value", aggfunc="mean")
        pivot = pivot.dropna()
        if 0 not in pivot.columns or max(selected_weeks) not in pivot.columns:
            return self._empty_result("inference", "No hay suficientes semanas para calcular crecimiento.")

        pivot["growth_pct"] = (pivot[0] - pivot[max(selected_weeks)]) / pivot[max(selected_weeks)]
        top = pivot.sort_values("growth_pct", ascending=False).head(10).reset_index()

        explanations = []
        metrics_to_check = [
            "Perfect Orders",
            "Gross Profit UE",
            "Restaurants SS > ATC CVR",
            "Lead Penetration",
        ]
        for _, row in top.iterrows():
            possible_drivers = []
            for metric_name in metrics_to_check:
                metric_df = self._base_filter(
                    {
                        "country": row["COUNTRY"],
                        "city": row["CITY"],
                        "zone": row["ZONE"],
                        "filters": {},
                    },
                    metric_override=metric_name,
                )
                metric_pivot = metric_df.pivot_table(index=["COUNTRY", "CITY", "ZONE"], columns="week_index", values="value", aggfunc="mean")
                if 0 in metric_pivot.columns and max(selected_weeks) in metric_pivot.columns:
                    delta = metric_pivot.iloc[0][0] - metric_pivot.iloc[0][max(selected_weeks)]
                    if delta > 0:
                        possible_drivers.append(metric_name)
            explanations.append(", ".join(possible_drivers[:2]) if possible_drivers else "Sin driver claro en las metricas observadas")

        top["possible_explanation"] = explanations
        title = f"Zonas con mayor crecimiento de Orders en ultimas {timeframe} semanas"
        summary = "El analisis marca asociaciones observacionales, no causalidad. Se listan posibles metricas que mejoraron en paralelo al crecimiento de Orders."
        return AnalysisResult("inference", title, top, summary, chart_type="bar")

    def _run_problematic_zones(self, query: Dict[str, object]) -> AnalysisResult:
        # Scoring simple: promediamos deterioro reciente en metricas donde mayor es mejor.
        current = self.df[self.df["week_index"] == 0].copy()
        prev = self.df[self.df["week_index"] == 1].copy()
        merged = pd.merge(
            current[["COUNTRY", "CITY", "ZONE", "METRIC", "value"]].rename(columns={"value": "current_value"}),
            prev[["COUNTRY", "CITY", "ZONE", "METRIC", "value"]].rename(columns={"value": "prev_value"}),
            on=["COUNTRY", "CITY", "ZONE", "METRIC"],
            how="inner",
        )
        if query.get("country"):
            merged = merged[merged["COUNTRY"] == query["country"]]

        merged["delta"] = merged["current_value"] - merged["prev_value"]

        def deterioration_score(row: pd.Series) -> float:
            higher_is_better = METRIC_METADATA.get(row["METRIC"], {}).get("higher_is_better", True)
            return -row["delta"] if higher_is_better else row["delta"]

        merged["deterioration_score"] = merged.apply(deterioration_score, axis=1)
        score_df = (
            merged.groupby(["COUNTRY", "CITY", "ZONE"], as_index=False)["deterioration_score"]
            .mean()
            .sort_values("deterioration_score", ascending=False)
            .head(10)
        )
        title = "Zonas problematicas"
        summary = "Se priorizan zonas con mayor deterioro promedio reciente considerando si cada metrica es deseable al alza o a la baja."
        return AnalysisResult("problematic_zones", title, score_df, summary, chart_type="bar")

    def _empty_result(self, kind: str, summary: str) -> AnalysisResult:
        return AnalysisResult(kind, "Sin resultados", pd.DataFrame(), summary, chart_type=None)
