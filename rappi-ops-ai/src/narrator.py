"""Narrativa en lenguaje natural sin depender de LLM.

Usamos templates para mantener consistencia, precision y una salida
ejecutiva / estilo consultor.
"""

from __future__ import annotations

import pandas as pd

from src.analytics_engine import AnalysisResult


def summarize_analysis(result: AnalysisResult) -> str:
    """Genera una respuesta ejecutiva en espanol a partir del resultado."""
    if result.dataframe.empty:
        return result.summary

    df = result.dataframe

    if result.kind == "ranking":
        top_row = df.iloc[0]
        metric_name = _extract_metric_name(result.summary)
        top_n = len(df)

        response = (
            f"Se muestran las {top_n} zonas con mejor desempeno en {metric_name} para la semana actual. "
            f"La zona lider es {top_row['ZONE']} ({top_row['CITY']}, {top_row['COUNTRY']}) "
            f"con un valor de {top_row['value']:.4f}."
        )

        if len(df) > 1:
            last_row = df.iloc[-1]
            gap = float(top_row["value"]) - float(last_row["value"])
            response += f" La brecha entre la primera y la quinta posicion es de {gap:.4f}."

        response += (
            " Esto sugiere una concentracion relevante del desempeno en pocas zonas, "
            "por lo que conviene revisar si estas lideres tambien sostienen mejor conversion, "
            "Perfect Orders u Orders."
        )
        return response

    if result.kind == "comparison":
        metric_name = _extract_metric_name(result.summary)

        label_col = None
        for col in df.columns:
            if col != "value":
                label_col = col
                break

        if label_col is None:
            return f"Se realizo una comparacion para {metric_name}."

        parts = [f"{row[label_col]}: {row['value']:.4f}" for _, row in df.iterrows()]
        joined = " | ".join(parts)

        response = (
            f"Comparacion promedio de {metric_name} en la semana actual agrupada por {label_col}. "
            f"Resultados principales: {joined}."
        )

        if len(df) >= 2:
            best_idx = df["value"].idxmax()
            worst_idx = df["value"].idxmin()
            best_row = df.loc[best_idx]
            worst_row = df.loc[worst_idx]
            diff = float(best_row["value"]) - float(worst_row["value"])

            response += (
                f" En esta vista, {best_row[label_col]} muestra mejor desempeno promedio que "
                f"{worst_row[label_col]} por {diff:.4f} puntos."
            )

            response += (
                " Esto puede ser util para priorizar analisis de brechas operativas, "
                "calidad de experiencia o diferencias estructurales entre segmentos."
            )

        return response

    if result.kind == "trend":
        metric_name = _extract_metric_name(result.summary)

        ordered = df.sort_values("week_index", ascending=False).copy()
        start_value = float(ordered.iloc[0]["value"])
        end_value = float(ordered.iloc[-1]["value"])
        delta = end_value - start_value

        if abs(delta) < 1e-6:
            direction_text = "estabilidad relativa"
            delta_text = "sin cambio material"
        elif delta > 0:
            direction_text = "mejora neta"
            delta_text = f"de {delta:.4f}"
        else:
            direction_text = "caida neta"
            delta_text = f"de {abs(delta):.4f}"

        response = (
            f"Serie temporal de {metric_name} para las ultimas {len(ordered)} semanas disponibles. "
            f"Entre el inicio y el final de la ventana se observa una {direction_text} {delta_text}."
        )

        peak_idx = ordered["value"].idxmax()
        trough_idx = ordered["value"].idxmin()
        peak_row = ordered.loc[peak_idx]
        trough_row = ordered.loc[trough_idx]

        response += (
            f" El valor maximo observado en la ventana fue {peak_row['value']:.4f} "
            f"(semana indice {int(peak_row['week_index'])}) y el minimo fue {trough_row['value']:.4f} "
            f"(semana indice {int(trough_row['week_index'])})."
        )

        response += (
            " Conviene revisar si este patron acompana cambios en Orders, Perfect Orders o metricas "
            "de conversion para entender si se trata de una variacion aislada o de una tendencia operativa."
        )

        return response

    if result.kind == "multivariable":
        metric_a, metric_b = _extract_two_metrics(result.summary)
        response = (
            f"Se identificaron {len(df)} zonas que combinan {metric_a} alto con {metric_b} bajo."
        )

        if not df.empty and "ZONE" in df.columns and "COUNTRY" in df.columns:
            sample = df.iloc[0]
            response += (
                f" Un caso representativo es {sample['ZONE']} ({sample['COUNTRY']}), "
                "que aparece como oportunidad clara de intervencion."
            )

        response += (
            " Este cruce es util para detectar zonas donde existe potencial comercial, "
            "pero la experiencia operativa o la conversion todavia no acompanan."
        )
        return response

    if result.kind == "inference":
        sample = df.iloc[0]
        response = (
            f"La zona con mayor crecimiento reciente detectado es {sample['ZONE']} ({sample['COUNTRY']}) "
            f"con crecimiento de {sample['growth_pct']:.1%}."
        )

        if "possible_explanation" in sample and pd.notna(sample["possible_explanation"]):
            response += f" Posibles drivers asociados: {sample['possible_explanation']}."

        response += (
            " Esta lectura debe interpretarse como una asociacion heuristica y no como causalidad. "
            "Aun asi, sirve para priorizar que variables conviene investigar primero."
        )
        return response

    if result.kind == "problematic_zones":
        sample = df.iloc[0]
        response = (
            f"La zona con mayor score de deterioro reciente es {sample['ZONE']} "
            f"({sample['CITY']}, {sample['COUNTRY']})."
        )
        response += (
            " Estas zonas merecen revision prioritaria porque concentran senales recientes de deterioro "
            "que pueden impactar experiencia, conversion o rentabilidad."
        )
        return response

    return result.summary


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 10) -> str:
    if df.empty:
        return "No hay filas para mostrar."
    return df.head(max_rows).to_markdown(index=False)


def _extract_metric_name(summary: str) -> str:
    """Intenta rescatar el nombre de la metrica desde el summary del motor."""
    known_metrics = [
        "% PRO Users Who Breakeven",
        "% Restaurants Sessions With Optimal Assortment",
        "Gross Profit UE",
        "Lead Penetration",
        "MLTV Top Verticals Adoption",
        "Non-Pro PTC > OP",
        "Perfect Orders",
        "Pro Adoption (Last Week Status)",
        "Restaurants Markdowns / GMV",
        "Restaurants SS > ATC CVR",
        "Restaurants SST > SS CVR",
        "Retail SST > SS CVR",
        "Turbo Adoption",
        "Orders",
    ]

    summary_lower = summary.lower()
    for metric in known_metrics:
        if metric.lower() in summary_lower:
            return metric

    return "la metrica solicitada"


def _extract_two_metrics(summary: str) -> tuple[str, str]:
    """Extrae hasta dos metricas conocidas desde un summary."""
    known_metrics = [
        "% PRO Users Who Breakeven",
        "% Restaurants Sessions With Optimal Assortment",
        "Gross Profit UE",
        "Lead Penetration",
        "MLTV Top Verticals Adoption",
        "Non-Pro PTC > OP",
        "Perfect Orders",
        "Pro Adoption (Last Week Status)",
        "Restaurants Markdowns / GMV",
        "Restaurants SS > ATC CVR",
        "Restaurants SST > SS CVR",
        "Retail SST > SS CVR",
        "Turbo Adoption",
        "Orders",
    ]

    found = []
    summary_lower = summary.lower()
    for metric in known_metrics:
        if metric.lower() in summary_lower:
            found.append(metric)

    if len(found) >= 2:
        return found[0], found[1]
    if len(found) == 1:
        return found[0], "otra metrica"
    return "una metrica", "otra metrica"
