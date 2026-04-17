"""Motor de insights automaticos.

Genera hallazgos ejecutivos con reglas claras y explicables.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from src.metric_catalog import METRIC_METADATA, country_display_name


class InsightsEngine:
    def __init__(self, unified_long: pd.DataFrame) -> None:
        self.df = unified_long.copy()

    def generate_all_insights(self) -> Dict[str, List[Dict[str, object]]]:
        return {
            "executive_summary": self._executive_summary(),
            "anomalies": self._anomalies(),
            "worrying_trends": self._worrying_trends(),
            "benchmarking": self._benchmarking(),
            "correlations": self._correlations(),
            "opportunities": self._opportunities(),
        }

    def _anomalies(self) -> List[Dict[str, object]]:
        current = self.df[self.df["week_index"] == 0]
        prev = self.df[self.df["week_index"] == 1]
        merged = pd.merge(
            current[["COUNTRY", "CITY", "ZONE", "METRIC", "value"]].rename(columns={"value": "current_value"}),
            prev[["COUNTRY", "CITY", "ZONE", "METRIC", "value"]].rename(columns={"value": "prev_value"}),
            on=["COUNTRY", "CITY", "ZONE", "METRIC"],
        )
        merged = merged[merged["prev_value"] != 0]
        merged["pct_change"] = (merged["current_value"] - merged["prev_value"]) / merged["prev_value"]
        anomalies = merged[np.abs(merged["pct_change"]) >= 0.10].copy()
        anomalies["impact_score"] = np.abs(anomalies["pct_change"])
        anomalies = anomalies.sort_values("impact_score", ascending=False).head(10)

        result = []
        for _, row in anomalies.iterrows():
            direction = "mejora" if row["pct_change"] > 0 else "deterioro"
            result.append({
                "category": "Anomaly",
                "title": f"{row['ZONE']} ({row['METRIC']}) presenta {direction} WoW",
                "finding": f"Cambio semanal de {row['pct_change']:.1%} en {row['METRIC']} en {row['ZONE']}, {country_display_name(row['COUNTRY'])}.",
                "impact": "Puede requerir validacion operativa o un deep dive puntual para entender el driver.",
                "recommendation": "Revisar el cambio con el owner de la zona y validar si fue efecto operacional, promocional o de medicion.",
                "score": float(row["impact_score"]),
            })
        return result

    def _worrying_trends(self) -> List[Dict[str, object]]:
        insights = []
        grouped = self.df.groupby(["COUNTRY", "CITY", "ZONE", "METRIC"])
        for (country, city, zone, metric), group in grouped:
            group = group.sort_values("week_index", ascending=False)
            if len(group) < 4:
                continue
            values = group["value"].tolist()[:4]
            deltas = [values[i] - values[i + 1] for i in range(len(values) - 1)]
            higher_is_better = METRIC_METADATA.get(metric, {}).get("higher_is_better", True)
            deteriorating = all(delta < 0 for delta in deltas) if higher_is_better else all(delta > 0 for delta in deltas)
            if deteriorating:
                insights.append({
                    "category": "Worrying trend",
                    "title": f"{zone} acumula 3 semanas de deterioro en {metric}",
                    "finding": f"La zona {zone} ({country_display_name(country)}) muestra una tendencia consistente de deterioro en {metric} durante las ultimas 3 transiciones semanales.",
                    "impact": "Indica un problema persistente y no un ruido puntual.",
                    "recommendation": "Priorizar una revision de causas raiz y contrastar contra zonas comparables del mismo pais y tipo.",
                    "score": float(abs(sum(deltas))),
                })
        insights.sort(key=lambda x: x["score"], reverse=True)
        return insights[:10]

    def _benchmarking(self) -> List[Dict[str, object]]:
        current = self.df[self.df["week_index"] == 0]
        # Excluimos orders para comparar calidad operativa entre pares mas homogeneos.
        current = current[current["METRIC"] != "Orders"]
        grouped = current.groupby(["COUNTRY", "ZONE_TYPE", "METRIC"])
        insights = []
        for (country, zone_type, metric), group in grouped:
            zone_avg = group.groupby("ZONE", as_index=False)["value"].mean()
            benchmark = zone_avg["value"].mean()
            zone_avg["gap_vs_peer"] = zone_avg["value"] - benchmark
            high_gap = zone_avg.loc[zone_avg["gap_vs_peer"].abs().idxmax()]
            if abs(high_gap["gap_vs_peer"]) > 0.08:
                insights.append({
                    "category": "Benchmarking",
                    "title": f"{high_gap['ZONE']} diverge de sus pares en {metric}",
                    "finding": f"Dentro de {country_display_name(country)} / {zone_type}, la zona {high_gap['ZONE']} se separa del promedio de sus pares en {metric} por {high_gap['gap_vs_peer']:.2f} puntos.",
                    "impact": "Puede señalar una mejor practica replicable o una brecha de performance a corregir.",
                    "recommendation": "Comparar drivers locales, playbooks y condiciones operativas frente al benchmark del segmento.",
                    "score": float(abs(high_gap["gap_vs_peer"])),
                })
        insights.sort(key=lambda x: x["score"], reverse=True)
        return insights[:10]

    def _correlations(self) -> List[Dict[str, object]]:
        current = self.df[self.df["week_index"] == 0]
        pivot = current.pivot_table(index=["COUNTRY", "CITY", "ZONE"], columns="METRIC", values="value", aggfunc="mean")
        candidate_pairs = [
            ("Lead Penetration", "Perfect Orders"),
            ("Lead Penetration", "Orders"),
            ("Perfect Orders", "Orders"),
            ("Restaurants SS > ATC CVR", "Orders"),
        ]
        insights = []
        for left, right in candidate_pairs:
            if left in pivot.columns and right in pivot.columns:
                corr = pivot[left].corr(pivot[right])
                if pd.notna(corr) and abs(corr) >= 0.25:
                    relation = "positiva" if corr > 0 else "negativa"
                    insights.append({
                        "category": "Correlation",
                        "title": f"Relacion {relation} entre {left} y {right}",
                        "finding": f"A nivel zona, {left} y {right} muestran una correlacion {relation} de {corr:.2f} en la semana actual.",
                        "impact": "Sirve para priorizar metricas palanca sobre el volumen o la calidad operativa.",
                        "recommendation": "Validar si esta relacion se sostiene por pais y usarla para priorizar experimentos operativos.",
                        "score": float(abs(corr)),
                    })
        insights.sort(key=lambda x: x["score"], reverse=True)
        return insights[:10]

    def _opportunities(self) -> List[Dict[str, object]]:
        insights = []
        current = self.df[self.df["week_index"] == 0]
        orders = current[current["METRIC"] == "Orders"].copy()
        perfect = current[current["METRIC"] == "Perfect Orders"].copy()
        lead = current[current["METRIC"] == "Lead Penetration"].copy()

        merged = orders.merge(perfect[["COUNTRY", "CITY", "ZONE", "value"]], on=["COUNTRY", "CITY", "ZONE"], suffixes=("_orders", "_perfect"))
        merged = merged.merge(lead[["COUNTRY", "CITY", "ZONE", "value"]], on=["COUNTRY", "CITY", "ZONE"])
        merged = merged.rename(columns={"value": "lead_penetration"})
        if not merged.empty:
            merged["opportunity_score"] = (1 - merged["value_perfect"]) * merged["value_orders"]
            top = merged.sort_values("opportunity_score", ascending=False).head(10)
            for _, row in top.iterrows():
                insights.append({
                    "category": "Opportunity",
                    "title": f"Mejorar Perfect Orders en {row['ZONE']} podria tener alto impacto",
                    "finding": f"{row['ZONE']} combina alto volumen de Orders con margen de mejora en Perfect Orders.",
                    "impact": "Una mejora moderada en calidad operativa podria mover una base importante de volumen.",
                    "recommendation": "Priorizar iniciativas de cancelaciones, defectos y tiempos en esa zona para capturar volumen de forma mas saludable.",
                    "score": float(row["opportunity_score"]),
                })
        insights.sort(key=lambda x: x["score"], reverse=True)
        return insights[:10]

    def _executive_summary(self) -> List[Dict[str, object]]:
        buckets = [
            self._anomalies(),
            self._worrying_trends(),
            self._benchmarking(),
            self._correlations(),
            self._opportunities(),
        ]
        flattened = [item for bucket in buckets for item in bucket]
        flattened.sort(key=lambda x: x.get("score", 0), reverse=True)
        return flattened[:5]
