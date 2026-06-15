# Importaciones estándar y de librerías
import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de la raíz del proyecto para las importaciones modulares
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.modules import config  
from src.modules.lambda_calculator import LambdaCalculator
from src.modules.hierarchy_generator import HierarchyGenerator

# 🌟 Configuración de la página con estilo limpio y expandido
st.set_page_config(page_title="Simulador Mundial 2026", page_icon="⚽", layout="wide")

# Estilo CSS minimalista para eliminar decoraciones innecesarias
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {font-weight: 300; letter-spacing: -1px;}
    .stButton>button {background-color: #111111; color: white; border-radius: 4px; border: none;}
    .stButton>button:hover {background-color: #333333; color: white;}
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Predictor Estocástico de Fútbol")
st.caption("Motor de simulación basado en Distribución de Poisson, Rankings oficiales y Valores de Mercado reales.")

# Inicializamos las jerarquías y cargamos los países disponibles
HierarchyGenerator.initialize()
paises_disponibles = sorted(list(HierarchyGenerator._market_values.keys()))

if not paises_disponibles:
    st.error("❌ No se pudo cargar la lista de países desde market_values.csv")
    st.stop()

# 🗂️ Creación de Pestañas de Navegación Planas
tab1, tab2 = st.tabs(["📊 Enfrentamiento Directo", "🏆 Simulación del Torneo"])

# ==========================================
# PESTAÑA 1: VERSUS DIRECTO (100K SIMULACIONES)
# ==========================================
with tab1:
    st.subheader("Configurar Partido Individual")
    
    col_a, col_b = st.columns(2)
    with col_a:
        local = st.selectbox("Selecciona Equipo Local", paises_disponibles, index=paises_disponibles.index("France") if "France" in paises_disponibles else 0)
    with col_b:
        visita = st.selectbox("Selecciona Equipo Visitante", paises_disponibles, index=paises_disponibles.index("Japan") if "Japan" in paises_disponibles else 1)
        
    if st.button("Correr Predicción Simétrica"):
        if local == visita:
            st.warning("⚠️ Selecciona dos países diferentes para la simulación.")
        else:
            with st.spinner("Ejecutando 100,000 simulaciones estocásticas..."):
                try:
                    # 1. Carga de data financiera
                    file_path = os.path.join(config.DATA_DIR, "market_values.csv")
                    df_market = pd.read_csv(file_path)
                    
                    data_local = df_market[df_market['team'] == local]
                    data_visita = df_market[df_market['team'] == visita]
                    
                    if not data_local.empty and not data_visita.empty:
                        st.markdown(f"""
                        <div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #111;'>
                            <strong>📊 Análisis de Kilates (Once Titular vs Banca):</strong><br>
                            • <strong>{local}</strong> — Once: {data_local['top11_value'].values[0]}M | Banca: {data_local['bench_value'].values[0]}M<br>
                            • <strong>{visita}</strong> — Once: {data_visita['top11_value'].values[0]}M | Banca: {data_visita['bench_value'].values[0]}M
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 2. Obtención de Lambdas
                    calculator = LambdaCalculator(local, visita)
                    lambda_local, lambda_visita = calculator.calculate_lambdas()
                    
                    # 🎲 3. BUCLE MUNDIAL DE 100,000 ITERACIONES DE MONTE CARLO EN CALIENTE
                    NUM_SIMULATIONS = 100000
                    sim_goles_local = np.random.poisson(lambda_local, NUM_SIMULATIONS)
                    sim_goles_visita = np.random.poisson(lambda_visita, NUM_SIMULATIONS)
                    
                    v_local = np.sum(sim_goles_local > sim_goles_visita)
                    v_visita = np.sum(sim_goles_visita > sim_goles_local)
                    empates = np.sum(sim_goles_local == sim_goles_visita)
                    
                    p_local = (v_local / NUM_SIMULATIONS) * 100
                    p_visita = (v_visita / NUM_SIMULATIONS) * 100
                    p_empate = (empates / NUM_SIMULATIONS) * 100
                    
                    # 4. Renderizado de la matriz analítica teórica para el Heatmap
                    max_goles = 8
                    goles_rango = np.arange(0, max_goles)
                    prob_local = poisson.pmf(goles_rango, lambda_local)
                    prob_visita = poisson.pmf(goles_rango, lambda_visita)
                    matriz_conjunta = np.outer(prob_local, prob_visita)
                    
                    st.write("---")
                    st.markdown(f"### Tasas de Gol Esperadas (λ): **{local}** ({lambda_local:.2f}) vs **{visita}** ({lambda_visita:.2f})")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric(f"Victoria {local}", f"{p_local:.1f}%")
                    m2.metric("Empate", f"{p_empate:.1f}%")
                    m3.metric(f"Victoria {visita}", f"{p_visita:.1f}%")
                    st.caption(f"🎯 Porcentajes validados mediante la ley de grandes números con {NUM_SIMULATIONS:,} simulaciones.")
                    
                    st.write("---")
                    st.subheader("🎯 Matriz de Probabilidad de Marcador Exacto")
                    
                    fig, ax = plt.subplots(figsize=(6, 4.5))
                    sns.heatmap(
                        matriz_conjunta[:6, :6], annot=True, fmt=".1%", cmap="Greys", 
                        xticklabels=goles_rango[:6], yticklabels=goles_rango[:6], cbar=False, ax=ax
                    )
                    ax.set_xlabel(f"Goles de {visita}")
                    ax.set_ylabel(f"Goles de {local}")
                    st.pyplot(fig)
                    
                except Exception as e:
                    st.error(f"Ocurrió un problema al procesar los Lambdas: {e}")

# ==========================================
# PESTAÑA 2: SIMULACIÓN DEL TORNEO MACRO
# ==========================================
with tab2:
    st.subheader("Simulación Estocástica del Mundial 2026")
    st.write("Corre un modelo de Monte Carlo para simular el torneo completo repetidamente en segundo plano.")
    
    # Selector de iteraciones macro para la copa
    num_sim = st.slider("Número de iteraciones del torneo", min_value=100, max_value=2000, value=1000, step=100)
    
    if st.button("🚀 Lanzar Simulación Global"):
        from src.predict_tournament import TournamentSimulator
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        simulator = TournamentSimulator(num_simulations=num_sim)
        
        def update_progress(current, total):
            pct = current / total
            progress_bar.progress(pct)
            status_text.text(f"Simulando Fixture: {current}/{total} torneos ejecutados...")
            
        with st.spinner("Procesando llaves en el motor estocástico..."):
            df_top_10 = simulator.run_monte_carlo(progress_callback=update_progress)
            
        status_text.success(f"🎉 ¡Simulación de {num_sim} Mundiales completada de forma exitosa!")
        
        st.write("---")
        st.subheader("🏆 Top 10 Favoritos a ganar la Copa del Mundo")
        
        fig_macro, ax_macro = plt.subplots(figsize=(7, 4))
        sns.barplot(
            x="prob_campeon", y="team", data=df_top_10,
            palette="Greys_r", ax=ax_macro
        )
        ax_macro.set_xlabel("Probabilidad de ser Campeón (%)")
        ax_macro.set_ylabel("Selección Nacional")
        sns.despine()
        
        st.pyplot(fig_macro)
        
        st.dataframe(
            df_top_10.style.format({"prob_campeon": "{:.1f}%"}),
            hide_index=True, use_container_width=True
        )