"""Generacion de reportes ejecutivos en Markdown y HTML."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List



def _render_insight(insight: Dict[str, object]) -> str:
    return (
        f"### {insight['title']}\n"
        f"- **Finding:** {insight['finding']}\n"
        f"- **Impacto:** {insight['impact']}\n"
        f"- **Recomendacion:** {insight['recommendation']}\n"
    )



def build_markdown_report(insights: Dict[str, List[Dict[str, object]]]) -> str:
    lines = [
        "# Rappi Operations AI - Executive Report",
        "",
        "## Resumen ejecutivo",
        "",
    ]
    for insight in insights.get("executive_summary", []):
        lines.append(_render_insight(insight))

    section_map = {
        "anomalies": "Anomalias",
        "worrying_trends": "Tendencias preocupantes",
        "benchmarking": "Benchmarking",
        "correlations": "Correlaciones",
        "opportunities": "Oportunidades",
    }
    for key, section_title in section_map.items():
        lines.append(f"\n## {section_title}\n")
        for insight in insights.get(key, []):
            lines.append(_render_insight(insight))
    return "\n".join(lines)



def markdown_to_basic_html(markdown_text: str) -> str:
    # Conversion simple y suficiente para el caso tecnico.
    html = markdown_text
    html = html.replace("# ", "<h1>").replace("\n## ", "<h2>")
    html = html.replace("\n### ", "<h3>")
    html = html.replace("**", "<b>")
    html = html.replace("- ", "<li>")
    html = html.replace("\n", "<br>\n")
    return f"<html><body>{html}</body></html>"



def write_reports(output_dir: str | Path, markdown_text: str, html_text: str) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "executive_report.md"
    html_path = output_dir / "executive_report.html"
    md_path.write_text(markdown_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    return md_path, html_path
