"""CLI de respaldo para la demo.

Ejemplos:
    python cli.py ask "Cuales son las 5 zonas con mayor Lead Penetration esta semana?"
    python cli.py insights
"""

from __future__ import annotations

import argparse

from src.analytics_engine import AnalyticsEngine
from src.data_loader import get_available_entities, load_data
from src.insights_engine import InsightsEngine
from src.narrator import dataframe_to_markdown, summarize_analysis
from src.query_parser import QueryParser
from src.report_generator import build_markdown_report, markdown_to_basic_html, write_reports
from src.utils import DATA_PATH, REPORTS_DIR



def build_system():
    bundle = load_data(DATA_PATH)
    countries, cities, zones, metrics = get_available_entities(bundle)
    parser = QueryParser(countries, cities, zones, metrics)
    analytics = AnalyticsEngine(bundle.unified_long)
    insights = InsightsEngine(bundle.unified_long)
    return parser, analytics, insights



def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Rappi Operations AI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser("ask", help="Hace una pregunta al motor analitico")
    ask_parser.add_argument("question", type=str, help="Pregunta en lenguaje natural")

    subparsers.add_parser("insights", help="Genera el reporte automatico")

    args = parser.parse_args()
    query_parser, analytics_engine, insights_engine = build_system()

    if args.command == "ask":
        parsed = query_parser.parse(args.question).to_dict()
        parsed["last_intent"] = parsed.get("intent")
        result = analytics_engine.run(parsed)
        print("\n=== RESPUESTA ===\n")
        print(summarize_analysis(result))
        print("\n=== TABLA ===\n")
        print(dataframe_to_markdown(result.dataframe))
    elif args.command == "insights":
        insights = insights_engine.generate_all_insights()
        md = build_markdown_report(insights)
        html = markdown_to_basic_html(md)
        md_path, html_path = write_reports(REPORTS_DIR, md, html)
        print(f"Reporte Markdown: {md_path}")
        print(f"Reporte HTML: {html_path}")


if __name__ == "__main__":
    run_cli()
