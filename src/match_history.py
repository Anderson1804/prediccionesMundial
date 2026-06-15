import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def get_complete_dataset():
    """Descarga el set de datos limpio desde Supabase para hacer las búsquedas"""
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    local_path = os.path.join("data", "clean_matches.csv")
    if not os.path.exists(local_path):
        print("📥 Descargando histórico completo desde Supabase...")
        res = supabase.storage.from_("datasets").download("clean_matches.csv")
        with open(local_path, "wb") as f:
            f.write(res)
            
    df = pd.read_csv(local_path)
    df['match_date'] = pd.to_datetime(df['match_date'])
    return df

def show_team_last_15(df, team):
    """Filtra y muestra los últimos 15 partidos oficiales de una selección"""
    # Buscamos partidos donde el equipo haya sido local O visitante
    team_matches = df[(df['home_team'] == team) | (df['away_team'] == team)]
    team_matches = team_matches.sort_values(by='match_date', ascending=False).head(15)
    
    print(f"\n📋 ÚLTIMOS 15 PARTIDOS OFICIALES DE {team.upper()}:")
    print("-" * 75)
    print(f"{'Fecha':<12} | {'Local':<20} | {'Score':<7} | {'Visitante':<20} | {'Torneo':<20}")
    print("-" * 75)
    
    for _, row in team_matches.iterrows():
        score = f"{row['home_score']}-{row['away_score']}"
        date_str = row['match_date'].strftime('%Y-%m-%d')
        print(f"{date_str:<12} | {row['home_team']:<20} | {score:<7} | {row['away_team']:<20} | {row['tournament'][:20]:<20}")
    print("-" * 75)

def show_head_to_head(df, team_a, team_b):
    """Busca TODO el historial histórico entre ambos equipos (Cara a Cara)"""
    # Caso 1: A es local y B es visitante | Caso 2: B es local y A es visitante
    h2h_matches = df[
        ((df['home_team'] == team_a) & (df['away_team'] == team_b)) |
        ((df['home_team'] == team_b) & (df['away_team'] == team_a))
    ]
    h2h_matches = h2h_matches.sort_values(by='match_date', ascending=False)
    
    print(f"\n⚔️ HISTORIAL HISTÓRICO CARA A CARA (HEAD-TO-HEAD): {team_a.upper()} vs {team_b.upper()}")
    print("=" * 75)
    
    if h2h_matches.empty:
        print("   ⚠️ No se registran partidos oficiales entre estas dos selecciones en la base de datos.")
        print("=" * 75)
        return
        
    print(f"{'Fecha':<12} | {'Local':<20} | {'Score':<7} | {'Visitante':<20} | {'Torneo':<20}")
    print("-" * 75)
    
    wins_a = 0
    wins_b = 0
    draws = 0
    
    for _, row in h2h_matches.iterrows():
        score = f"{row['home_score']}-{row['away_score']}"
        date_str = row['match_date'].strftime('%Y-%m-%d')
        print(f"{date_str:<12} | {row['home_team']:<20} | {score:<7} | {row['away_team']:<20} | {row['tournament'][:20]:<20}")
        
        # Contabilizar estadísticas históricas
        if row['home_score'] > row['away_score']:
            if row['home_team'] == team_a: wins_a += 1
            else: wins_b += 1
        elif row['home_score'] < row['away_score']:
            if row['away_team'] == team_a: wins_a += 1
            else: wins_b += 1
        else:
            draws += 1
            
    print("-" * 75)
    print(f"📊 RESUMEN HISTÓRICO:")
    print(f"   • Victorias de {team_a}: {wins_a}")
    print(f"   • Victorias de {team_b}: {wins_b}")
    print(f"   • Empates: {draws}")
    print("=" * 75)

if __name__ == "__main__":
    try:
        df_all = get_complete_dataset()
        
        print("\n🔍 --- BIENVENIDO AL BUSCADOR DE HISTORIALES ---")
        # Recuerda ingresar los nombres en inglés acorde al dataset (ej. Brazil, Morocco, Peru)
        team_1 = input("⚽ Ingresa la primera selección (ej. Brazil): ").strip()
        team_2 = input("⚽ Ingresa la segunda selección (ej. Morocco): ").strip()
        
        # 1. Desplegar los 15 partidos individuales de cada uno
        show_team_last_15(df_all, team_1)
        show_team_last_15(df_all, team_2)
        
        # 2. Desplegar el cara a cara completo de la historia
        show_head_to_head(df_all, team_1, team_2)
        
        input("\n🏁 Presiona ENTER para salir...")
    except Exception as e:
        print(f"❌ Ocurrió un error en la búsqueda: {e}")
        input()