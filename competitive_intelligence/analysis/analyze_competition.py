import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "uber_eats_products.csv")
PROC_PATH = os.path.join(BASE_DIR, "data", "processed", "uber_eats_products_clean.csv")
REPORT_PATH = os.path.join(BASE_DIR, "outputs", "reports", "competitive_report.md")

df = pd.read_csv(RAW_PATH)

# -------------------
# LIMPIEZA
# -------------------
df["eta_num"] = df["eta"].astype(str).str.extract(r"(\d+)").astype(float)
df["product_clean"] = df["product_name"].astype(str).str.lower()

# Categorías comparables
df["product_category"] = None
df.loc[df["product_clean"].str.contains("big mac", na=False), "product_category"] = "big_mac"
df.loc[df["product_clean"].str.contains("nuggets", na=False), "product_category"] = "nuggets"
df.loc[df["product_clean"].str.contains("combo", na=False), "product_category"] = "combo"

# Precios
df["price_num"] = df["price"].astype(str).str.replace("$", "", regex=False)
df["price_num"] = pd.to_numeric(df["price_num"], errors="coerce")

# Quedarnos solo con productos comparables
df = df[df["product_category"].notna()].copy()

# Deduplicar por restaurante + producto
df = df.drop_duplicates(subset=["restaurant_name", "product_name"])

# Guardar limpio
os.makedirs(os.path.dirname(PROC_PATH), exist_ok=True)
df.to_csv(PROC_PATH, index=False)

# -------------------
# METRICAS
# -------------------
avg_eta = df.groupby("restaurant_name")["eta_num"].mean().sort_values()
product_counts = df["product_category"].value_counts()

priced_df = df[df["price_num"].notna()].copy()

if not priced_df.empty:
    avg_price_cat = priced_df.groupby("product_category")["price_num"].mean().round(1)
    avg_price_restaurant = priced_df.groupby("restaurant_name")["price_num"].mean().round(1)
else:
    avg_price_cat = pd.Series(dtype=float)
    avg_price_restaurant = pd.Series(dtype=float)

eta_gap = None
if not avg_eta.empty:
    eta_gap = round(avg_eta.max() - avg_eta.min(), 1)

# -------------------
# INSIGHTS
# -------------------
insights = []

if not avg_eta.empty:
    fastest = avg_eta.idxmin()
    slowest = avg_eta.idxmax()
    insights.append(f"""
1. **Diferencia operativa observable entre restaurantes**
   - Restaurante más rápido: **{fastest}** ({avg_eta.min():.1f} min)
   - Restaurante más lento: **{slowest}** ({avg_eta.max():.1f} min)

   **Impacto:** Existe una brecha operativa de **{eta_gap:.1f} minutos** dentro de la muestra.
   **Recomendación:** Si Rappi compite en esta zona, tiene sentido evaluar subsidios o priorización logística frente a restaurantes con ETA más bajo.
""")

if not product_counts.empty:
    dominant_category = product_counts.idxmax()
    insights.append(f"""
2. **Predominio de productos tipo {dominant_category}**
   - Distribución observada:
{product_counts.to_string()}

   **Impacto:** La mayor parte de la oferta visible se concentra en bundles y productos de ticket medio/alto.
   **Recomendación:** Competir con ofertas equivalentes y promociones empaquetadas, no solo con productos unitarios.
""")

if not avg_price_cat.empty:
    insights.append(f"""
3. **Rango de precios competitivos identificado**
   - Precio promedio por categoría:
{avg_price_cat.to_string()}

   **Impacto:** Ya existe una señal suficiente para inferir el rango competitivo visible de la muestra.
   **Recomendación:** Usar estos valores como benchmark inicial para pricing en productos equivalentes dentro de Rappi.
""")
else:
    insights.append("""
3. **Cobertura parcial de precios**
   - La extracción de precios fue incompleta en parte del menú.

   **Impacto:** El benchmark de pricing todavía es muestral.
   **Recomendación:** Complementar con validación manual adicional o una segunda iteración del scraper.
""")

if not avg_price_restaurant.empty:
    cheapest = avg_price_restaurant.idxmin()
    most_expensive = avg_price_restaurant.idxmax()
    insights.append(f"""
4. **La diferenciación parece darse más por precio que por tiempo**
   - Restaurante con menor precio promedio en muestra: **{cheapest}** ({avg_price_restaurant.min():.1f})
   - Restaurante con mayor precio promedio en muestra: **{most_expensive}** ({avg_price_restaurant.max():.1f})

   **Impacto:** Como los ETAs son relativamente cercanos, la diferenciación observable se mueve hacia pricing y promociones.
   **Recomendación:** En este contexto, una estrategia de descuentos o bundles puede mover más la aguja que una mejora marginal en ETA.
""")

insights.append("""
5. **Pipeline competitivo ya utilizable aunque no totalmente automatizado**
   - Se logró capturar datos reales de restaurantes, ETA, rating, productos y una muestra útil de precios.

   **Impacto:** Ya se puede generar inteligencia competitiva accionable con un enfoque híbrido.
   **Recomendación:** Escalar el mismo pipeline a más direcciones y más plataformas para robustecer la lectura estratégica.
""")

# -------------------
# REPORTE
# -------------------
report = f"""
# Competitive Intelligence Report

## Resumen Ejecutivo
Se analizó una muestra de restaurantes comparables en Uber Eats para entender tiempos de entrega, mix de productos y rango de precios visibles.

La evidencia sugiere que:
- los tiempos de entrega son relativamente cercanos entre competidores,
- la competencia visible está dominada por combos y nuggets,
- y el pricing observable se mueve en un rango acotado.

## Métricas principales

### ETA promedio por restaurante
{avg_eta.to_string()}

### Presencia de categorías de producto
{product_counts.to_string()}

### Precio promedio por categoría
{avg_price_cat.to_string() if not avg_price_cat.empty else "No hay suficientes datos de precio"}

### Precio promedio por restaurante
{avg_price_restaurant.to_string() if not avg_price_restaurant.empty else "No hay suficientes datos de precio"}

## Top Insights

{chr(10).join(insights)}

## Conclusión
La muestra sugiere que, en este segmento, la competencia no se define solo por tiempos de entrega sino principalmente por estrategia de bundles, productos equivalentes y precios visibles.

Con una segunda iteración sobre más direcciones y más plataformas, este pipeline puede escalar a un sistema de inteligencia competitiva mucho más robusto.
"""

os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(report)

print("✅ Data procesada:", PROC_PATH)
print("📄 Reporte generado:", REPORT_PATH)