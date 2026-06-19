import os
import sys
import pandas as pd

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")

def fusionar_base_maestra_tactica():
    print("📋 ================= FUSIÓN MAESTRA TÁCTICA ================= 📋")
    
    # Rutas de tus archivos reales
    jugadores_valores_path = os.path.join(DATA_DIR, "jugadores_valores.csv")
    estadisticas_kaggle_path = os.path.join(DATA_DIR, "estadisticas_kaggle.csv") # El que bajas de Kaggle
    output_path = os.path.join(DATA_DIR, "jugadores_maestro_tactico.csv")
    
    # Generación de archivo ficticio de estadísticas si no existe
    if not os.path.exists(estadisticas_kaggle_path):
        print("⚠️ No se encontró 'estadisticas_kaggle.csv'. Creando un set de pruebas estocástico...")
        # Simulamos las columnas de Sofascore/Kaggle para que pruebes el pipeline YA
        df_valores = pd.read_csv(jugadores_valores_path)
        
        df_mock = pd.DataFrame({
            'player': df_valores['player'],
            'rating_global': pd.Series(0.0).repeat(len(df_valores)).apply(lambda x: round(pd.np.random.uniform(6.5, 8.4), 2)),
            'goles_promedio': pd.Series(0.0).repeat(len(df_valores)).apply(lambda x: round(pd.np.random.uniform(0.0, 0.7), 2)),
            'asistencias_promedio': pd.Series(0.0).repeat(len(df_valores)).apply(lambda x: round(pd.np.random.uniform(0.0, 0.5), 2)),
            'recuperaciones_promedio': pd.Series(0.0).repeat(len(df_valores)).apply(lambda x: round(pd.np.random.uniform(0.5, 4.2), 2))
        })
        df_mock.to_csv(estadisticas_kaggle_path, index=False)
        print("✅ Archivo de estadísticas simuladas creado en data/estadisticas_kaggle.csv")

    # 1. Carga de Dataframes
    df_jugadores = pd.read_csv(jugadores_valores_path)
    df_kaggle = pd.read_csv(estadisticas_kaggle_path)
    
    print(f"📊 Registros originales en tu base: {len(df_jugadores)}")
    
    # Cruce de datos por el identificador del jugador (player)
    df_maestro = pd.merge(df_jugadores, df_kaggle, on="player", how="left")
    
    # Imputar valores por defecto en registros con datos faltantes
    df_maestro['rating_global'] = df_maestro['rating_global'].fillna(7.0)
    df_maestro['goles_promedio'] = df_maestro['goles_promedio'].fillna(0.1)
    df_maestro['asistencias_promedio'] = df_maestro['asistencias_promedio'].fillna(0.1)
    df_maestro['recuperaciones_promedio'] = df_maestro['recuperaciones_promedio'].fillna(1.5)
    
    # 4. Exportar el producto final de ingeniería
    df_maestro.to_csv(output_path, index=False)
    print(f"🚀 ¡Base Maestra Creada con éxito en: {output_path}!")
    print(df_maestro[['team', 'player', 'position', 'value', 'rating_global', 'goles_promedio']].head())

if __name__ == "__main__":
    fusionar_base_maestra_tactica()