import os
import sys
import numpy as np
import pandas as pd

# Configuración de rutas para correr desde la raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.modules import config
from src.modules.lambda_calculator import LambdaCalculator

def run_console_prediction(team_home, team_away):
    print("\n========================================================")
    print(f"📊 AUDITORÍA DE PARTIDO (CONSOLA): {team_home} vs {team_away}")
    print("========================================================")
    
    try:
        # 1. Cargar y mostrar la segmentación financiera real de las plantillas
        file_path = os.path.join(config.DATA_DIR, "market_values.csv")
        df_market = pd.read_csv(file_path)
        
        data_local = df_market[df_market['team'] == team_home]
        data_visita = df_market[df_market['team'] == team_away]
        
        if not data_local.empty and not data_visita.empty:
            print(f"💰 [Once Titular] {team_home}: {data_local['top11_value'].values[0]}M | {team_away}: {data_visita['top11_value'].values[0]}M")
            print(f"🪑 [Profundidad Banca] {team_home}: {data_local['bench_value'].values[0]}M | {team_away}: {data_visita['bench_value'].values[0]}M")
            print("--------------------------------------------------------")
            
        # 2. Calcular los Lambdas dinámicos
        calculator = LambdaCalculator(team_home, team_away)
        lambda_local, lambda_visita = calculator.calculate_lambdas()
        
        print(f"⚽ Goles Esperados (λ): {team_home} ({lambda_local}) vs {team_away} ({lambda_visita})")
        print("--------------------------------------------------------")
        
        # 🚀 3. SIMULACIÓN DE MONTE CARLO (100,000 ITERACIONES EXPLÍCITAS)
        NUM_SIMULATIONS = 100000
        print(f"🎲 Ejecutando {NUM_SIMULATIONS:,} simulaciones estocásticas de Poisson...")
        
        # Generamos 100,000 resultados aleatorios de goles basados en los lambdas
        sim_goles_local = np.random.poisson(lambda_local, NUM_SIMULATIONS)
        sim_goles_visita = np.random.poisson(lambda_visita, NUM_SIMULATIONS)
        
        # Contabilizamos cuántas veces ganó cada uno o hubo empate
        victorias_local = np.sum(sim_goles_local > sim_goles_visita)
        victorias_visita = np.sum(sim_goles_visita > sim_goles_local)
        empates = np.sum(sim_goles_local == sim_goles_visita)
        
        # Convertimos a porcentajes
        p_local = (victorias_local / NUM_SIMULATIONS) * 100
        p_visita = (victorias_visita / NUM_SIMULATIONS) * 100
        p_empate = (empates / NUM_SIMULATIONS) * 100
        
        # 4. Despliegue de Resultados en Consola
        print(f"🟢 Probabilidad Victoria {team_home}: {p_local:.1f}%")
        print(f"⚪ Probabilidad Empate: {p_empate:.1f}%")
        print(f"🔵 Probabilidad Victoria {team_away}: {p_visita:.1f}%")
        print("========================================================\n")
        
    except Exception as e:
        print(f"❌ Error al procesar la simulación en consola: {e}")

if __name__ == "__main__":
    run_console_prediction("Túnez", "Suecia")