# Sistema de Inteligencia Competitiva para Rappi

## Descripción
Este proyecto implementa un pipeline de scraping y análisis competitivo sobre plataformas de delivery, con foco en entender tiempos de entrega, mix de productos y rango de precios visibles.

La solución fue diseñada para funcionar en un entorno real con restricciones anti-bot, por lo que utiliza un enfoque híbrido humano-asistido para asegurar robustez y reproducibilidad.

## Objetivo
Generar insights accionables para equipos de Pricing, Operations y Strategy a partir de datos competitivos recolectados en plataformas de delivery.

## Alcance implementado
- Plataforma trabajada: Uber Eats
- Zona inicial: Guadalajara
- Restaurantes comparables:
  - KFC (Juárez-736)
  - McDonald's Centro
  - Burger King (Centro GDL)
- Variables capturadas:
  - `restaurant_name`
  - `rating`
  - `eta`
  - `product_name`
  - `price`
  - `url`
  - `scrape_time`

## Enfoque
Dado que las plataformas reales utilizan mecanismos anti-bot como CAPTCHA, se priorizó un enfoque híbrido:
- el usuario define dirección y navega manualmente,
- el sistema captura datos estructurados,
- luego se ejecuta una capa automática de limpieza, categorización y análisis.

Este enfoque permitió privilegiar estabilidad y reproducibilidad frente a una automatización total más frágil.

## Estructura del proyecto
- `scrapers/`: lógica de scraping
- `analysis/`: limpieza y generación de insights
- `data/raw/`: datos crudos
- `data/processed/`: datos limpios
- `outputs/reports/`: reporte final

## Cómo ejecutar

### 1. Instalar dependencias

pip install -r requirements.txt
python -m playwright install

### 2. Ejecutar scraper

python scrapers/scraper_uber.py

### 3. Ejecutar analisis

python analysis/analyze_competition.py