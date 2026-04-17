"""Funciones de graficacion para Streamlit y reportes."""

from __future__ import annotations

import pandas as pd
import plotly.express as px

from src.analytics_engine import AnalysisResult



def build_chart(result: AnalysisResult):
    df = result.dataframe.copy()
    if df.empty or not result.chart_type:
        return None

    if result.chart_type == "bar":
        x_col = df.columns[0]
        y_col = df.columns[-1]
        return px.bar(df, x=x_col, y=y_col, title=result.title)

    if result.chart_type == "line":
        return px.line(df.sort_values("week_index"), x="week_index", y="value", title=result.title, markers=True)

    if result.chart_type == "scatter":
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        if len(numeric_cols) >= 2:
            return px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], hover_name="ZONE", title=result.title)
    return None
