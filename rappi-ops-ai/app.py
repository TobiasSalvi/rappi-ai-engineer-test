"""Aplicacion Streamlit principal.

Ejecucion:
    python -m streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src.analytics_engine import AnalyticsEngine
from src.charting import build_chart
from src.conversation_memory import ConversationMemory
from src.data_loader import get_available_entities, load_data
from src.insights_engine import InsightsEngine
from src.narrator import dataframe_to_markdown, summarize_analysis
from src.query_parser import QueryParser
from src.report_generator import build_markdown_report, markdown_to_basic_html, write_reports
from src.utils import DATA_PATH, REPORTS_DIR


@st.cache_resource
def build_system():
    bundle = load_data(DATA_PATH)
    countries, cities, zones, metrics = get_available_entities(bundle)
    parser = QueryParser(countries, cities, zones, metrics)
    analytics = AnalyticsEngine(bundle.unified_long)
    insights = InsightsEngine(bundle.unified_long)
    return bundle, parser, analytics, insights


def run_analysis(question: str) -> None:
    """Ejecuta una pregunta, actualiza memoria e historial."""
    if not question or not question.strip():
        return

    parsed = parser.parse(question).to_dict()
    parsed["last_intent"] = parsed.get("intent")
    hydrated = st.session_state.memory.hydrate(parsed)
    result = analytics.run(hydrated)
    answer = summarize_analysis(result)

    st.session_state.memory.update_from_query(hydrated)
    st.session_state.chat_history.append(
        {
            "question": question,
            "answer": answer,
            "result": result,
        }
    )
    st.session_state.user_question = question


st.set_page_config(page_title="IA de operaciones de Rappi", layout="wide")
st.title("IA de operaciones de Rappi")
st.caption("Bot conversacional e insights automáticos para operaciones.")

bundle, parser, analytics, insights_engine = build_system()

if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_question" not in st.session_state:
    st.session_state.user_question = ""

with st.sidebar:
    st.header("Preguntas sugeridas")
    suggestions = [
        "Cuales son las 5 zonas con mayor Lead Penetration esta semana?",
        "Compara Perfect Orders entre zonas Wealthy y Non Wealthy en Mexico",
        "Muestra la evolucion de Gross Profit UE en Chapinero ultimas 8 semanas",
        "Cual es el promedio de Lead Penetration por pais?",
        "Que zonas tienen alto Lead Penetration pero bajo Perfect Orders?",
        "Cuales son las zonas que mas crecen en ordenes en las ultimas 5 semanas y que podria explicar el crecimiento?",
        "Cuales son las zonas problematicas en Colombia?",
    ]

    for idx, suggestion in enumerate(suggestions):
        if st.button(suggestion, key=f"suggestion_{idx}", use_container_width=True):
            run_analysis(suggestion)

    st.divider()
    st.header("Reporte ejecutivo")
    if st.button("Generar reporte automatico", use_container_width=True):
        insights = insights_engine.generate_all_insights()
        md = build_markdown_report(insights)
        html = markdown_to_basic_html(md)
        md_path, html_path = write_reports(REPORTS_DIR, md, html)
        st.success("Reporte generado correctamente.")
        st.write(f"Markdown: {md_path}")
        st.write(f"HTML: {html_path}")

col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("Chat de análisis")

    with st.form("analysis_form", clear_on_submit=False):
        user_question = st.text_input(
            "Escribe tu pregunta",
            value=st.session_state.user_question,
            placeholder="Ej: Compara Perfect Orders entre Wealthy y Non Wealthy en Mexico",
        )
        submitted = st.form_submit_button("Analizar", type="primary")

    if submitted:
        run_analysis(user_question)

    if st.session_state.chat_history:
        latest_item = st.session_state.chat_history[-1]

        st.markdown("### Última respuesta")
        st.markdown(f"**Usuario:** {latest_item['question']}")
        st.markdown(f"**Sistema:** {latest_item['answer']}")

        if not latest_item["result"].dataframe.empty:
            st.markdown(dataframe_to_markdown(latest_item["result"].dataframe))

        previous_items = st.session_state.chat_history[:-1]
        if previous_items:
            with st.expander("Ver historial anterior"):
                for item in reversed(previous_items):
                    st.markdown(f"**Usuario:** {item['question']}")
                    st.markdown(f"**Sistema:** {item['answer']}")
                    if not item["result"].dataframe.empty:
                        st.markdown(dataframe_to_markdown(item["result"].dataframe))
                    st.divider()
    else:
        st.info("Escribe una pregunta o usa una sugerencia para comenzar.")

with col2:
    st.subheader("Visualización")
    if st.session_state.chat_history:
        latest_result = st.session_state.chat_history[-1]["result"]
        chart = build_chart(latest_result)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("La consulta actual no tiene gráfico sugerido.")
    else:
        st.info("Hace una consulta para ver aquí la visualización sugerida.")