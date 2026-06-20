import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Orígenes Crudos
PATH_RESULTS_RAW = os.path.join(DATA_DIR, "results.csv")
PATH_GOALS_RAW = os.path.join(DATA_DIR, "goalscore.csv")
PATH_RANK_RAW = os.path.join(DATA_DIR, "teams_elo_ranking.csv")
PATH_VAL_RAW = os.path.join(DATA_DIR, "jugadores_valores.csv")
PATH_GROUPS_RAW = os.path.join(DATA_DIR, "world_cup_groups.csv") # Fixture oficial del torneo

# Destinos Universales Purificados en Español
PATH_RESULTS_OUT = os.path.join(DATA_DIR, "clean_results.csv")
PATH_GOALS_OUT = os.path.join(DATA_DIR, "clean_goalscores.csv")
PATH_RANK_OUT = os.path.join(DATA_DIR, "clean_rankings.csv")
PATH_VAL_OUT = os.path.join(DATA_DIR, "clean_jugadores_valores.csv")

FECHA_CORTE_MUNDIAL = "2026-06-11"

# Diccionario de normalización y traducción de nombres de países

DIC_UNIVERSAL = {
    "france": "Francia", "germany": "Alemania", "spain": "España", "brazil": "Brasil",
    "england": "Inglaterra", "italy": "Italia", "netherlands": "Países Bajos", 
    "belgium": "Bélgica", "croatia": "Croacia", "morocco": "Marruecos", "japan": "Japón", 
    "usa": "Estados Unidos", "united states": "Estados Unidos", "mexico": "México", 
    "canada": "Canadá", "peru": "Perú", "saudi arabia": "Arabia Saudita", 
    "egypt": "Egipto", "algeria": "Argelia", "tunisia": "Túnez", 
    "switzerland": "Suiza", "denmark": "Dinamarca", "poland": "Polonia", 
    "sweden": "Suecia", "norway": "Noruega", "ukraine": "Ucrania", 
    "turkey": "Turquía", "new zealand": "Nueva Zelanda", "argentina": "Argentina", 
    "portugal": "Portugal", "jordan": "Jordania",
    "dr congo": "RD Congo", "congo dr": "RD Congo", "congo": "RD Congo", 
    "república democrática del congo": "RD Congo", "republica democratica del congo": "RD Congo",
    "panama": "Panamá", "panamá": "Panamá", "ghana": "Ghana", "uzbekistan": "Uzbekistán", "uzbekistán": "Uzbekistán",
    "south korea": "Corea del Sur", "korea republic": "Corea del Sur", "korea south": "Corea del Sur", "corea del sur": "Corea del Sur",
    
    #  REGULARIZACIÓN EVOLUTIVA PARA HAITÍ:
    "haiti": "Haití",
    "haití": "Haití",

    # Normalización del nombre de Corea del Sur
    "south korea": "Corea del Sur",
    "korea republic": "Corea del Sur",
    "korea south": "Corea del Sur",
    "corea del sur": "Corea del Sur",
    "ivory coast": "Costa de Marfil",
    "cote d'ivoire": "Costa de Marfil",
    "côte d'ivoire": "Costa de Marfil",
    "costa de marfil": "Costa de Marfil"
}

def normalizar_pais(nombre):
    if pd.isna(nombre): return "Desconocido"
    nombre_limpio = str(nombre).strip().lower()
    return DIC_UNIVERSAL.get(nombre_limpio, str(nombre).strip().title())

def cargar_csv(path):
    try:
        return pd.read_csv(path, sep=None, encoding='utf-8-sig', on_bad_lines='skip', engine='python')
    except Exception:
        return pd.read_csv(path, sep=None, encoding='latin-1', on_bad_lines='skip', engine='python')

def obtener_paises_mundialistas():
    """Extrae y normaliza el universo estricto de los 48 clasificados al Mundial."""
    df_g = cargar_csv(PATH_GROUPS_RAW)
    if df_g is None:
        return set()
    df_g.columns = df_g.columns.astype(str).str.strip().str.lower()
    col_team = next((c for c in df_g.columns if 'team' in c or 'equipo' in c or 'pais' in c), df_g.columns[0])
    return set(df_g[col_team].apply(normalizar_pais))

# Funciones de procesamiento de datos con filtro de selecciones participantes

def procesar_results(paises_validos):
    print("⏳ Estandarizando 'results.csv'...")
    df = cargar_csv(PATH_RESULTS_RAW)
    if df is None: return
    df.columns = df.columns.astype(str).str.strip().str.lower()
    
    col_date = next((c for c in df.columns if 'date' in c or 'fecha' in c), df.columns[0])
    col_home = next((c for c in df.columns if 'home_team' in c or 'home' in c), df.columns[1])
    col_away = next((c for c in df.columns if 'away_team' in c or 'away' in c), df.columns[2])
    col_h_score = next((c for c in df.columns if 'home_score' in c), df.columns[3])
    col_a_score = next((c for c in df.columns if 'away_score' in c), df.columns[4])
    col_tournament = next((c for c in df.columns if 'tournament' in c), df.columns[5])

    df_clean = pd.DataFrame()
    df_clean['date'] = pd.to_datetime(df[col_date], errors='coerce')
    df_clean['home_team'] = df[col_home].apply(normalizar_pais)
    df_clean['away_team'] = df[col_away].apply(normalizar_pais)
    df_clean['home_score'] = pd.to_numeric(df[col_h_score], errors='coerce')
    df_clean['away_score'] = pd.to_numeric(df[col_a_score], errors='coerce')
    df_clean['tournament'] = df[col_tournament].astype(str).str.strip()

    df_clean = df_clean.dropna(subset=['date', 'home_team', 'away_team', 'home_score', 'away_score'])
    df_final = df_clean[df_clean['date'] < pd.to_datetime(FECHA_CORTE_MUNDIAL)].copy()
    
    # Solo guardamos partidos que involucren al menos a un mundialista para optimizar peso
    df_final = df_final[df_final['home_team'].isin(paises_validos) | df_final['away_team'].isin(paises_validos)]
    df_final.to_csv(PATH_RESULTS_OUT, index=False, encoding='utf-8')
    print(f"✅ 'clean_results.csv' generado ({df_final.shape[0]} filas).")

def procesar_goalscores(paises_validos):
    print("⏳ Estandarizando 'goalscore.csv'...")
    df = cargar_csv(PATH_GOALS_RAW)
    if df is None: return
    df.columns = df.columns.astype(str).str.strip().str.lower()

    df_clean = pd.DataFrame()
    df_clean['date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
    df_clean['home_team'] = df.iloc[:, 1].apply(normalizar_pais)
    df_clean['away_team'] = df.iloc[:, 2].apply(normalizar_pais)
    df_clean['team'] = df.iloc[:, 3].apply(normalizar_pais)
    df_clean['scorer'] = df.iloc[:, 4].astype(str).str.strip()
    df_clean['minute'] = pd.to_numeric(df.iloc[:, 5], errors='coerce')
    df_clean['own_goal'] = df.iloc[:, 6].astype(str).str.lower().str.contains('t|1')
    df_clean['penalty'] = df.iloc[:, 7].astype(str).str.lower().str.contains('t|1')

    df_clean = df_clean.dropna(subset=['team', 'scorer'])
    # Filtro estricto de selecciones mundialistas
    df_clean = df_clean[df_clean['team'].isin(paises_validos)]
    df_clean.to_csv(PATH_GOALS_OUT, index=False, encoding='utf-8')
    print(f"✅ 'clean_goalscores.csv' generado ({df_clean.shape[0]} filas).")

def procesar_rankings(paises_validos):
    print("⏳ Estandarizando 'teams_elo_ranking.csv'...")
    df = cargar_csv(PATH_RANK_RAW)
    if df is None: return
    df.columns = df.columns.astype(str).str.strip().str.lower()

    df_clean = pd.DataFrame()
    df_clean['team'] = df.iloc[:, 0].apply(normalizar_pais)
    df_clean['elo'] = pd.to_numeric(df.iloc[:, 1], errors='coerce')
    df_clean = df_clean.dropna(subset=['team', 'elo'])
    
    # Filtrar únicamente los países clasificados para el torneo
    df_final = df_clean[df_clean['team'].isin(paises_validos)].copy()
    df_final.to_csv(PATH_RANK_OUT, index=False, encoding='utf-8')
    print(f"✅ 'clean_rankings.csv' generado. Solo {df_final.shape[0]} países mundialistas indexados.")

def procesar_jugadores(paises_validos):
    print("⏳ Estandarizando 'jugadores_valores.csv'...")
    df = cargar_csv(PATH_VAL_RAW)
    if df is None: return
    df.columns = df.columns.astype(str).str.strip().str.lower()

    df_clean = pd.DataFrame()
    df_clean['team'] = df.iloc[:, 0].apply(normalizar_pais)
    df_clean['player'] = df.iloc[:, 1].astype(str).str.strip()
    df_clean['value'] = pd.to_numeric(df.iloc[:, 2], errors='coerce')
    df_clean = df_clean.dropna(subset=['team', 'player', 'value'])
    
    df_final = df_clean[df_clean['team'].isin(paises_validos)].copy()
    df_final.to_csv(PATH_VAL_OUT, index=False, encoding='utf-8')
    print(f"✅ 'clean_jugadores_valores.csv' generado con éxito.")

if __name__ == "__main__":
    print("Iniciando procesamiento de limpieza de bases de datos mundialistas...")
    print("="*60)
    paises_mundialistas = obtener_paises_mundialistas()
    print(f"🏆 Detectados {len(paises_mundialistas)} países únicos en el fixture oficial del Mundial.")
    
    if len(paises_mundialistas) > 0:
        procesar_results(paises_mundialistas)
        procesar_goalscores(paises_mundialistas)
        procesar_rankings(paises_mundialistas)
        procesar_jugadores(paises_mundialistas)
        print("="*60)
        print("Procesamiento completado y ruido filtrado.")
    else:
        print("❌ Error: No se pudo procesar la lista de países mundialistas.")