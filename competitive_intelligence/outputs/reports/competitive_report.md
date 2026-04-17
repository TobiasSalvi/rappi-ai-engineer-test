
# Competitive Intelligence Report

## Resumen Ejecutivo
Se analizó una muestra de restaurantes comparables en Uber Eats para entender tiempos de entrega, mix de productos y rango de precios visibles.

La evidencia sugiere que:
- los tiempos de entrega son relativamente cercanos entre competidores,
- la competencia visible está dominada por combos y nuggets,
- y el pricing observable se mueve en un rango acotado.

## Métricas principales

### ETA promedio por restaurante
restaurant_name
KFC (Juárez-736)            10.0
McDonald's Centro           10.0
Burger King (Centro GDL)    13.0

### Presencia de categorías de producto
product_category
combo      23
nuggets    15
big_mac     4

### Precio promedio por categoría
product_category
big_mac     75.0
combo      101.3
nuggets     79.5

### Precio promedio por restaurante
restaurant_name
Burger King (Centro GDL)    102.8
KFC (Juárez-736)             94.4
McDonald's Centro            79.1

## Top Insights


1. **Diferencia operativa observable entre restaurantes**
   - Restaurante más rápido: **KFC (Juárez-736)** (10.0 min)
   - Restaurante más lento: **Burger King (Centro GDL)** (13.0 min)

   **Impacto:** Existe una brecha operativa de **3.0 minutos** dentro de la muestra.
   **Recomendación:** Si Rappi compite en esta zona, tiene sentido evaluar subsidios o priorización logística frente a restaurantes con ETA más bajo.


2. **Predominio de productos tipo combo**
   - Distribución observada:
product_category
combo      23
nuggets    15
big_mac     4

   **Impacto:** La mayor parte de la oferta visible se concentra en bundles y productos de ticket medio/alto.
   **Recomendación:** Competir con ofertas equivalentes y promociones empaquetadas, no solo con productos unitarios.


3. **Rango de precios competitivos identificado**
   - Precio promedio por categoría:
product_category
big_mac     75.0
combo      101.3
nuggets     79.5

   **Impacto:** Ya existe una señal suficiente para inferir el rango competitivo visible de la muestra.
   **Recomendación:** Usar estos valores como benchmark inicial para pricing en productos equivalentes dentro de Rappi.


4. **La diferenciación parece darse más por precio que por tiempo**
   - Restaurante con menor precio promedio en muestra: **McDonald's Centro** (79.1)
   - Restaurante con mayor precio promedio en muestra: **Burger King (Centro GDL)** (102.8)

   **Impacto:** Como los ETAs son relativamente cercanos, la diferenciación observable se mueve hacia pricing y promociones.
   **Recomendación:** En este contexto, una estrategia de descuentos o bundles puede mover más la aguja que una mejora marginal en ETA.


5. **Pipeline competitivo ya utilizable aunque no totalmente automatizado**
   - Se logró capturar datos reales de restaurantes, ETA, rating, productos y una muestra útil de precios.

   **Impacto:** Ya se puede generar inteligencia competitiva accionable con un enfoque híbrido.
   **Recomendación:** Escalar el mismo pipeline a más direcciones y más plataformas para robustecer la lectura estratégica.


## Conclusión
La muestra sugiere que, en este segmento, la competencia no se define solo por tiempos de entrega sino principalmente por estrategia de bundles, productos equivalentes y precios visibles.

Con una segunda iteración sobre más direcciones y más plataformas, este pipeline puede escalar a un sistema de inteligencia competitiva mucho más robusto.
