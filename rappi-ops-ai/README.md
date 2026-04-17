# Sistema de Análisis Inteligente para Operaciones

## Descripción
Este proyecto implementa un sistema de análisis conversacional para democratizar el acceso a métricas operativas y automatizar la generación de insights para equipos de Operations y Strategy.

La solución permite que usuarios no técnicos consulten datos en lenguaje natural y obtengan respuestas claras, estructuradas y accionables.

## Objetivo
Reducir la dependencia de análisis manuales repetitivos y facilitar la exploración de métricas operativas a través de una interfaz conversacional.

## Funcionalidades principales

### 1. Bot conversacional sobre datos
- Consultas en lenguaje natural
- Ranking de zonas o ciudades
- Comparaciones entre segmentos
- Tendencias temporales
- Detección de combinaciones de métricas
- Respuestas narrativas tipo negocio

### 2. Motor de insights automáticos
- Detección de anomalías
- Identificación de tendencias negativas
- Benchmarking entre entidades
- Hallazgos heurísticos
- Generación automática de reportes

### 3. Interfaces
- Aplicación web en Streamlit
- CLI como respaldo

## Arquitectura
Usuario → Parser de consultas → Motor analítico → Narrativa → UI → Motor de insights → Reporte                                             

## Stack tecnológico
- Python
- Pandas / NumPy
- Streamlit
- Plotly
- Parser basado en reglas
- Sin dependencia de LLM pago

## ¿Por qué no usar un LLM?
El problema es altamente estructurado:
- métricas conocidas
- datos tabulares
- tipos de consulta repetibles

Por eso se priorizó un enfoque determinístico que ofrece:
- mayor precisión
- reproducibilidad
- costo cero
- menor complejidad operativa

Se deja abierta la posibilidad de incorporar un LLM más adelante como capa opcional para mejorar flexibilidad semántica.

## Cómo ejecutar

### Aplicación web

pip install -r requirements.txt
python -m streamlit run app.py

### CLI

python cli.py ask "Cuales son las 5 zonas con mayor Lead Penetration esta semana?"