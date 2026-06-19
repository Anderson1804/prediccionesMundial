import os
import pandas as pd
from dotenv import load_dotenv
import kagglehub
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_tournament_weight(tournament):
    t_lower = tournament.lower()
    if 'fifa world cup' in t_lower and 'qualifying' not in t_lower:
        return 4.0  # Torneo Copa del Mundo
    elif 'copa américa' in t_lower or 'uefa euro' in t_lower:
        return 3.0  # Torneos continentales top
    elif 'qualifying' in t_lower or 'eliminatorias' in t_lower:
        return 2.5  # Clasificatorias de alta presión
    elif 'nations league' in t_lower:
        return 1.5  # Torneos oficiales regulares
    return 1.0      # Otros torneos oficiales menores

def download_and_clean_kaggle():
    print("Descargando dataset desde Kaggle...")
    download_path = kagglehub.dataset_download("martj42/international-football-results-from-1872-to-2017")
    csv_path = os.path.join(download_path, "results.csv")
    
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.rename(columns={'date': 'match_date', 'neutral': 'neutral_bool'})
    
    print("Filtrando partidos oficiales...")
    df_oficial = df[df['tournament'].str.lower() != 'friendly'].copy()
    
    # Asignar peso del torneo al DataFrame
    df_oficial['tournament_weight'] = df_oficial['tournament'].apply(get_tournament_weight)
    return df_oficial

def calculate_advanced_stats(df):
    print("Calculando promedios móviles de goles y puntos...")
    df = df.sort_values(by='match_date').reset_index(drop=True)
    
    team_goals_scored = {}
    team_goals_conceded = {}
    team_points = {} 
    
    home_sc_avg, away_sc_avg = [], []
    home_con_avg, away_con_avg = [], []
    home_form, away_form = [], []
    
    for idx, row in df.iterrows():
        h_team = row['home_team']
        a_team = row['away_team']
        h_score = row['home_score']
        a_score = row['away_score']
        
        for team, lst, target_list in [(h_team, team_goals_scored, home_sc_avg), (a_team, team_goals_scored, away_sc_avg)]:
            target_list.append(sum(lst.get(team, [])[-5:]) / len(lst.get(team, [0])[-5:]) if team in lst else 0.0)
            
        for team, lst, target_list in [(h_team, team_goals_conceded, home_con_avg), (a_team, team_goals_conceded, away_con_avg)]:
            target_list.append(sum(lst.get(team, [])[-5:]) / len(lst.get(team, [0])[-5:]) if team in lst else 0.0)
            
        for team, lst, target_list in [(h_team, team_points, home_form), (a_team, team_points, away_form)]:
            target_list.append(sum(lst.get(team, [])[-5:]) / len(lst.get(team, [0])[-5:]) if team in lst else 1.0)

        team_goals_scored.setdefault(h_team, []).append(h_score)
        team_goals_scored.setdefault(a_team, []).append(a_score)
        team_goals_conceded.setdefault(h_team, []).append(a_score)
        team_goals_conceded.setdefault(a_team, []).append(h_score)
        
        points = 3 if h_score > a_score else (1 if h_score == a_score else 0)
        team_points.setdefault(h_team, []).append(points)
        team_points.setdefault(a_team, []).append(3 if points == 0 else (1 if points == 1 else 0))

    df['home_goals_scored_avg'] = home_sc_avg
    df['away_goals_scored_avg'] = away_sc_avg
    df['home_goals_conceded_avg'] = home_con_avg
    df['away_goals_conceded_avg'] = away_con_avg
    df['home_form_avg'] = home_form
    df['away_form_avg'] = away_form
    
    return df

def filter_by_modern_era(df):
    print("Filtrando era moderna (desde 2018)...")
    return df[df['match_date'] >= '2018-01-01'].copy()

def upload_via_api(df):
    os.makedirs("data", exist_ok=True)
    local_csv_path = os.path.join("data", "clean_matches.csv")
    df.to_csv(local_csv_path, index=False)
    
    with open(local_csv_path, 'rb') as f:
        supabase.storage.from_("datasets").upload(file=f, path="clean_matches.csv", file_options={"upsert": "true"})
    print("Dataset con pesos de torneo procesado y subido.")

if __name__ == "__main__":
    try:
        df_cleaned = download_and_clean_kaggle()
        df_stats = calculate_advanced_stats(df_cleaned)
        df_filtered = filter_by_modern_era(df_stats)
        upload_via_api(df_filtered)
    except Exception as e:
        print(f"❌ Error: {e}")