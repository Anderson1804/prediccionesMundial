# 🎲 Sistema de Predicción Estocástica para el Mundial 2026

Este módulo implementa un motor de inferencia estadística basado en la **Distribución de Poisson** y **Simulaciones de Monte Carlo (10,000 iteraciones)** para predecir marcadores exactos de fútbol.

## 🧠 Modelo Matemático Avanzado: Densidad de Talento

A diferencia de los modelos predictivos convencionales que utilizan el valor bruto de una plantilla, este sistema implementa un algoritmo de **Segmentación Dinámica de Calidad (90/10)** para eliminar el ruido estadístico causado por jugadores que no suman minutos en cancha:

* **Once Titular ($Top 11$):** Controla el **90%** del impacto del valor de mercado, midiendo el poder de fuego real durante los 90 minutos reglamentarios.
* **Profundidad de Banca ($Bench$):** Sostiene el **10%** restante, evaluando la capacidad de recambio y consistencia física en el segundo tiempo.

### Campo Neutral Simétrico
El motor calcula los Lambdas ($\lambda$) de goles esperados bajo condiciones estrictas de torneo internacional, neutralizando el sesgo de localía ($1.50$ base simétrico) y cruzando tres variables vivas: **Puntaje ELO Histórico**, **Factor de Jerarquía de Liga** e **Índice de Impacto Financiero en Campo**.

## 📐 Arquitectura del Módulo (`src/`)
El sistema aplica principios de **Arquitectura Limpia** para separar las responsabilidades:
* `predict_match_poisson.py`: Orquestador y punto de entrada.
* `modules/config.py`: Parámetros de calibración global.
* `modules/lambda_calculator.py`: Brain matemático (Time Decay, Opponent Quality y FIFA Modifier).
* `modules/data_loader.py`: Capa de extracción y limpieza de datos (CSV).
* `utils/update_market_values.py`: Web Scraper avanzado y paginado (Top 100) que burla la seguridad de Transfermarkt para extraer el valor individual de los 26 convocados por selección.
* `app.py`: Interfaz gráfica interactiva y minimalista construida en Streamlit para la visualización de datos en tiempo real y exportación de reportes.
* `modules/visualizer.py`: Renderizado analítico de mapas de calor.

## 🚀 Instrucciones de Ejecución

1. **Actualizar el Ranking Global FIFA (Costo Cero / Web Scraping):**
   ```powershell
   python src/download_rankings.py
2. **Raspar Valores Detallados de Transfermarkt (Top 100 Selecciones):**
   ```powershell
   python src/utils/update_market_values.py
4. **Añadir una sección de "Features / Características Clave"**
Ideal para destacar la experiencia de usuario que lograste con los gráficos:

```markdown
## 🎯 Características Principales

* **Matriz de Poisson Interactiva:** Renderizado dinámico de mapas de calor en escala de grises con la probabilidad exacta de marcadores del 0-0 al 5-5.
* **Exportación Analítica:** Botón nativo de descarga en la UI para exportar el mapa de calor en alta definición (`.png` a 300 DPI) listo para reportes.
* **Consistencia de Datos:** Sincronización absoluta de strings en español entre el pipeline de scraping, el motor de consola y la interfaz web. 
![Dashboard Preview](assets/screenshot_dashboard.png)