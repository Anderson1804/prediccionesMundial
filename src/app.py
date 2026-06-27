# Importaciones estándar y de librerías
# 1. ENTRAR DIRECTO CON LOS IMPORTS NATIVOS DE PYTHON
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Tus módulos ya no se romperán porque el path se inyectó en la línea 2
from src.modules.tournament_simulator import TournamentSimulator
from src.modules.lambda_calculator import LambdaCalculator
# Configuración de la raíz del proyecto para las importaciones modulares
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.modules import config  
from src.modules.lambda_calculator import LambdaCalculator
from src.modules.hierarchy_generator import HierarchyGenerator
from src.modules.data_loader import DataLoader  # Carga de datos unificada

# Configuración de la aplicación Streamlit
st.set_page_config(page_title="Simulador Mundial 2026", page_icon="⚽", layout="wide")

# Estilos personalizados para métricas y botones
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {font-weight: 300; letter-spacing: -1px;}
    .stButton>button {background-color: #111111; color: white; border-radius: 4px; border: none; width: 100%;}
    .stButton>button:hover {background-color: #333333; color: white;}
    [data-testid="stMetricValue"] {font-size: 1.8rem; font-weight: 400;}
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Predictor Estocástico de Fútbol")
st.caption("Motor de simulación basado en Distribución de Poisson, Rankings oficiales y Ajustes Manuales de Plantel.")

# Carga de datos de jugadores y rankings
try:
    # Cargamos la data purificada nativa en Español
    df_jugadores = DataLoader.get_jugadores_valores()
    df_rankings = DataLoader.get_fifa_rankings()
    
    # Lista de países disponibles
    paises_disponibles = sorted(df_rankings['team'].unique().tolist())
    
except Exception as e:
    st.error(f"❌ Error al cargar las bases de datos estandarizadas: {e}")
    st.info("Mano, asegúrate de haber ejecutado primero en tu terminal: python src/clean_datasets.py")
    st.stop()


# Definición de pestañas de navegación
tab1, tab2 = st.tabs(["📊 Enfrentamiento Directo", "🏆 Simulación del Torneo"])

# Pestaña 1: Enfrentamiento directo
with tab1:
    st.subheader("Configurar Partido Individual")
    
    col_sel_a, col_sel_b = st.columns(2)
    with col_sel_a:
        local = st.selectbox("Selecciona Equipo Local", paises_disponibles, index=paises_disponibles.index("Portugal") if "Portugal" in paises_disponibles else 0)
    with col_sel_b:
        visita = st.selectbox("Selecciona Equipo Visitante", paises_disponibles, index=paises_disponibles.index("Argentina") if "Argentina" in paises_disponibles else min(1, len(paises_disponibles)-1))
        
    if local == visita:
        st.warning("⚠️ Selecciona dos países diferentes para la simulación.")
        st.stop()

    st.write("---")
    st.subheader("📋 Configuración Táctica Manual (Ajuste del Once Titular)")
    st.caption("Selecciona los 11 jugadores titulares. Los que no elijas pasarán automáticamente a la banca del modelo.")

    # Filtrar jugadores por equipo
    pool_local = df_jugadores[df_jugadores['team'] == local].sort_values(by='value', ascending=False)
    pool_visita = df_jugadores[df_jugadores['team'] == visita].sort_values(by='value', ascending=False)

    col_tack_a, col_tack_b = st.columns(2)
    
    with col_tack_a:
        st.markdown(f"### **{local}**")
        opciones_local = pool_local['player'].tolist()
        default_local = opciones_local[:11] if len(opciones_local) >= 11 else opciones_local
        titulares_local = st.multiselect(f"Once Titular - {local}", opciones_local, default=default_local, key="multiselect_local")
        
        df_tit_A = pool_local[pool_local['player'].isin(titulares_local)]
        df_ban_A = pool_local[~pool_local['player'].isin(titulares_local)]
        
        val_tit_A = df_tit_A['value'].sum()
        val_ban_A = df_ban_A['value'].sum()
        
        if len(titulares_local) != 11:
            st.caption(f"⚠️ Has seleccionado {len(titulares_local)} jugadores. Ajusta a 11 para un rendimiento óptimo.")

    with col_tack_b:
        st.markdown(f"### **{visita}**")
        opciones_visita = pool_visita['player'].tolist()
        default_visita = opciones_visita[:11] if len(opciones_visita) >= 11 else opciones_visita
        titulares_visita = st.multiselect(f"Once Titular - {visita}", opciones_visita, default=default_visita, key="multiselect_visita")
        
        df_tit_B = pool_visita[pool_visita['player'].isin(titulares_visita)]
        df_ban_B = pool_visita[~pool_visita['player'].isin(titulares_visita)]
        
        val_tit_B = df_tit_B['value'].sum()
        val_ban_B = df_ban_B['value'].sum()
        
        if len(titulares_visita) != 11:
            st.caption(f"⚠️ Has seleccionado {len(titulares_visita)} jugadores. Ajusta a 11 para un rendimiento óptimo.")

    st.write("---")
    st.markdown("### 💰 Análisis Comparativo de Kilates Financieros")
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric(f"Titulares {local}", f"${val_tit_A:.1f}M")
    metric_col2.metric(f"Banca {local}", f"${val_ban_A:.1f}M")
    metric_col3.metric(f"Titulares {visita}", f"${val_tit_B:.1f}M")
    metric_col4.metric(f"Banca {visita}", f"${val_ban_B:.1f}M")

    st.write("---")
    
    # Simulación del enfrentamiento
    if st.button("🚀 Correr Predicción Simétrica"):
        if len(titulares_local) == 0 or len(titulares_visita) == 0:
            st.error("❌ Debes seleccionar al menos un jugador en el once titular de cada equipo.")
        else:
            with st.spinner("Ejecutando 100,000 simulaciones estocásticas..."):
                try:
                    calculator = LambdaCalculator(local, visita)
                    
                    # Obtener estadísticas y parámetros de goles esperados (lambdas)
                    lambda_local, lambda_visita, stats_local, stats_visita = calculator.calculate_lambdas(
                        titulares_manual_home=titulares_local,
                        titulares_manual_away=titulares_visita
                    )
                    
                    # Mostrar rendimiento goleador real
                    st.markdown("### 📈 Rendimiento Goleador Real (Últimos 15 Partidos)")
                    hist_col1, hist_col2, hist_col3, hist_col4 = st.columns(4)
                    
                    hist_col1.metric(f"Goles Realizados {local}", f"{stats_local['gf']:.2f}")
                    hist_col2.metric(f"Goles Recibidos {local}", f"{stats_local['gc']:.2f}")
                    hist_col3.metric(f"Goles Realizados {visita}", f"{stats_visita['gf']:.2f}")
                    hist_col4.metric(f"Goles Recibidos {visita}", f"{stats_visita['gc']:.2f}")
                    
                    # Simulación de Monte Carlo
                    NUM_SIMULATIONS = 100000
                    sim_goles_local = np.random.poisson(lambda_local, NUM_SIMULATIONS)
                    sim_goles_visita = np.random.poisson(lambda_visita, NUM_SIMULATIONS)
                    
                    v_local = np.sum(sim_goles_local > sim_goles_visita)
                    v_visita = np.sum(sim_goles_visita > sim_goles_local)
                    empates = np.sum(sim_goles_local == sim_goles_visita)
                    
                    p_local = (v_local / NUM_SIMULATIONS) * 100
                    p_visita = (v_visita / NUM_SIMULATIONS) * 100
                    p_empate = (empates / NUM_SIMULATIONS) * 100
                    
                    max_goles = 8
                    goles_rango = np.arange(0, max_goles)
                    prob_local = poisson.pmf(goles_rango, lambda_local)
                    prob_visita = poisson.pmf(goles_rango, lambda_visita)
                    matriz_conjunta = np.outer(prob_local, prob_visita)
                    
                    st.write("---")
                    st.markdown(f"### Tasas de Gol Ajustadas Finales (λ): **{local}** ({lambda_local:.2f}) vs **{visita}** ({lambda_visita:.2f})")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric(f"Victoria {local}", f"{p_local:.1f}%")
                    m2.metric("Empate", f"{p_empate:.1f}%")
                    m3.metric(f"Victoria {visita}", f"{p_visita:.1f}%")
                    st.caption(f"🎯 Porcentajes validados mediante la ley de grandes números con {NUM_SIMULATIONS:,} simulaciones basadas en Ataque vs Defensa.")
                    
                    st.write("---")
                    # Matriz de probabilidad de marcador exacto
                    
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

# Pestaña 2: Simulación del torneo
with tab2:
    st.title("🏆 Simulación Estocástica del Mundial 2026")
    st.markdown("""
    Esta sección ejecuta un modelo de **Monte Carlo** para simular el fixture completo de la Copa del Mundo 
    (Fase de Grupos y Llaves de Eliminación Directa) analizando el rendimiento ofensivo, defensivo y financiero de los 48 clasificados.
    """)

    # 1. Cargar el fixture ya traducido al español por el ETL
    @st.cache_data
    def cargar_grupos_limpios():
        return pd.read_csv("data/clean_world_cup_groups.csv")

    df_groups = cargar_grupos_limpios()

    # 2. Control de parámetros para el usuario
    st.subheader("⚙️ Configuración del Experimento Estocástico")
    num_simulaciones = st.slider(
        "Selecciona la cantidad de Mundiales completos a simular (N):", 
        min_value=100, 
        max_value=2000, 
        value=1000, 
        step=100
    )

    # 3. Disparador de la simulación de Monte Carlo
    if st.button("🚀 Lanzar Simulación Global", icon="⚽"):
        with st.spinner(f"Simulando {num_simulaciones} copas del mundo en segundo plano..."):
            
            # Inicializamos el simulador con la data limpia
            simulador = TournamentSimulator(df_groups)
            
            # Diccionario contador de campeones
            conteo_campeones = {}
            
            # Bucle macro de Monte Carlo (Mundiales independientes)
            for _ in range(num_simulaciones):
                campeon_ficticio = simulador.run_full_tournament()
                conteo_campeones[campeon_ficticio] = conteo_campeones.get(campeon_ficticio, 0) + 1
                
            # Transformamos los resultados en un DataFrame estadístico
            df_resultados = pd.DataFrame(conteo_campeones.items(), columns=['Equipo', 'Copas'])
            
            # Aplicamos la Ley de los Grandes Números para hallar la Frecuencia Relativa (Probabilidad)
            df_resultados['Probabilidad'] = (df_resultados['Copas'] / num_simulaciones) * 100
            df_resultados = df_resultados.sort_values(by='Probabilidad', ascending=False).head(10)
            
        st.success("¡Simulación completada con éxito!")
        
        # =====================================================================
        # 📊 RENDERIZADO DEL GRÁFICO PROFESIONAL EN STREAMLIT
        # =====================================================================
        st.subheader("📊 Top 10 Candidatos al Título (Frecuencia de Éxito)")
        
        # Configuración del diseño minimalista y plano (estilo formal para tesis)
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#0e1117')  # Match con el fondo oscuro de Streamlit
        ax.set_facecolor('#0e1117')
        
        # Gráfico de barras horizontal limpio en escala de grises profesional
        sns.barplot(
            x='Probabilidad', 
            y='Equipo', 
            data=df_resultados, 
            palette='Greys_r',  # Gradiente minimalista plano sin colores chillones
            ax=ax
        )
        
        # Estilizado formal de etiquetas y rejillas
        ax.set_xlabel("Probabilidad de ser Campeón (%)", color="white", fontsize=11, fontweight="bold")
        ax.set_ylabel("Selección Nacional", color="white", fontsize=11, fontweight="bold")
        ax.tick_params(colors="white", labelsize=10)
        ax.xaxis.grid(True, linestyle="--", alpha=0.3, color="gray")
        ax.set_axisbelow(True)
        
        # Eliminar bordes (spines) decorativos innecesarios
        for spine in ax.spines.values():
            spine.set_visible(False)
            
        # Añadir los porcentajes de texto exactos al final de cada barra para mayor rigor analítico
        for index, value in enumerate(df_resultados['Probabilidad']):
            ax.text(value + 0.3, index, f"{value:.1f}%", color="white", va="center", fontsize=10, fontweight="bold")
            
        # Desplegar el gráfico de Matplotlib de forma nativa
        st.pyplot(fig)
        
        # Tabla de datos complementaria para auditar los números exactos
        st.subheader("📋 Matriz de Frecuencias Absolutas")
        st.dataframe(
            df_resultados[['Equipo', 'Copas', 'Probabilidad']].rename(
                columns={'Copas': 'Mundiales Ganados', 'Probabilidad': 'Probabilidad (%)'}
            ),
            use_container_width=True,
            hide_index=True
        )