import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Coeficientes de Confederación internacional para ajuste de peso de partidos
CONFEDERATION_COEFFICIENTS = {
    # CONMEBOL (Peso: 1.00)
    "Argentina": 1.00, "Brazil": 1.00, "Uruguay": 1.00, "Colombia": 1.00, "Ecuador": 1.00,
    "Peru": 1.00, "Chile": 1.00, "Paraguay": 1.00, "Venezuela": 1.00, "Bolivia": 1.00,
    
    # UEFA (Peso: 0.99)
    "Spain": 0.99, "France": 0.99, "England": 0.99, "Portugal": 0.99, "Netherlands": 0.99,
    "Croatia": 0.99, "Germany": 0.99, "Italy": 0.99, "Belgium": 0.99, "Switzerland": 0.99,
    "Wales": 0.99, "Denmark": 0.99, "Poland": 0.99, "Serbia": 0.99,
    
    # Confederaciones secundarias (CAF, CONCACAF, AFC)
    "Morocco": 0.85, "Senegal": 0.85, "Nigeria": 0.85, "Algeria": 0.85, "Tunisia": 0.85, "Cameroon": 0.85, "Ghana": 0.85,
    "Mexico": 0.85, "USA": 0.85, "United States": 0.85, "Panama": 0.85, "Costa Rica": 0.85, "Canada": 0.85,
    "Japan": 0.85, "Australia": 0.85, "South Korea": 0.85, "Iran": 0.85, "Uzbekistan": 0.85, "Jordan": 0.85, 
    "Saudi Arabia": 0.85, "Qatar": 0.85, "Iran": 0.85
}

def get_team_coeff(team):
    # Si un equipo menor no está en la lista top, le asignamos el peso base de confederaciones externas (0.85)
    return CONFEDERATION_COEFFICIENTS.get(team, 0.85)

def download_data_from_supabase():
    print("Descargando dataset de partidos desde Supabase...")
    local_path = os.path.join("data", "clean_matches.csv")
    with open(local_path, "wb") as f:
        res = supabase.storage.from_("datasets").download("clean_matches.csv")
        f.write(res)
    return pd.read_csv(local_path)

def calculate_expected_score(rating_a, rating_b):
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

def update_elo_ratings(df, k_factor=32):
    print("Calculando ratings Elo ajustados por Confederación...")
    
    all_teams = set(df['home_team'].unique()).union(set(df['away_team'].unique()))
    elo_dict = {team: 1500.0 for team in all_teams}
    
    df['match_date'] = pd.to_datetime(df['match_date'])
    df = df.sort_values(by='match_date').reset_index(drop=True)
    
    home_elos = []
    away_elos = []
    
    for idx, row in df.iterrows():
        home = row['home_team']
        away = row['away_team']
        
        home_elos.append(elo_dict[home])
        away_elos.append(elo_dict[away])
        
        we_home = calculate_expected_score(elo_dict[home], elo_dict[away])
        we_away = calculate_expected_score(elo_dict[away], elo_dict[home])
        
        if row['home_score'] > row['away_score']:
            w_home, w_away = 1.0, 0.0
        elif row['home_score'] < row['away_score']:
            w_home, w_away = 0.0, 1.0
        else:
            w_home, w_away = 0.5, 0.5
            
        # Aplicar el coeficiente de confederación a la diferencia de Elo
        coeff_home = get_team_coeff(home)
        coeff_away = get_team_coeff(away)
        combined_coeff = (coeff_home + coeff_away) / 2.0
        
        # El Factor K se modifica dinámicamente según la confederación de los rivales
        dynamic_k = k_factor * combined_coeff
        
        elo_dict[home] += dynamic_k * (w_home - we_home)
        elo_dict[away] += dynamic_k * (w_away - we_away)
        
    df['home_elo_before'] = home_elos
    df['away_elo_before'] = away_elos
    
    print("📈 Procesamiento de Elo con coeficientes completado.")
    
    ranking_df = pd.DataFrame(list(elo_dict.items()), columns=['team', 'elo_rating'])
    ranking_df = ranking_df.sort_values(by='elo_rating', ascending=False).reset_index(drop=True)
    
    return df, ranking_df

def save_and_upload_results(df_with_elo, ranking_df):
    os.makedirs("data", exist_ok=True)
    matches_path = os.path.join("data", "matches_with_elo.csv")
    ranking_path = os.path.join("data", "teams_elo_ranking.csv")
    
    df_with_elo.to_csv(matches_path, index=False)
    ranking_df.to_csv(ranking_path, index=False)
    
    with open(matches_path, 'rb') as f:
        supabase.storage.from_("datasets").upload(file=f, path="matches_with_elo.csv", file_options={"upsert": "true"})
    with open(ranking_path, 'rb') as f:
        supabase.storage.from_("datasets").upload(file=f, path="teams_elo_ranking.csv", file_options={"upsert": "true"})
    print("Cálculo y subida de datos Elo completado en Supabase.")

if __name__ == "__main__":
    try:
        df_matches = download_data_from_supabase()
        df_with_elo, ranking_df = update_elo_ratings(df_matches)
        save_and_upload_results(df_with_elo, ranking_df)
    except Exception as e:
        print(f"❌ Error en el generador de Elo: {e}")