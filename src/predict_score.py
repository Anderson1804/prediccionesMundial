import os
import numpy as np
import pandas as pd
from scipy.stats import poisson
import matplotlib.pyplot as plt

def get_team_stats():
    local_matches = os.path.join("data", "matches_with_elo.csv")
    if not os.path.exists(local_matches):
        raise FileNotFoundError("❌ No se encuentra el archivo de datos. Corre el pipeline primero.")
        
    df = pd.read_csv(local_matches)
    df['match_date'] = pd.to_datetime(df['match_date'])
    df = df.sort_values(by='match_date')
    
    stats_dict = {}
    for _, row in df.iterrows():
        stats_dict[row['home_team']] = {
            'elo': row['home_elo_before'], 
            'goals_sc': row['home_goals_scored_avg'],
            'goals_co': row['home_goals_conceded_avg']
        }
        stats_dict[row['away_team']] = {
            'elo': row['away_elo_before'], 
            'goals_sc': row['away_goals_scored_avg'],
            'goals_co': row['away_goals_conceded_avg']
        }
    return stats_dict

def predict_score_probability(team_home, team_away, stats):
    # Valores por defecto si el equipo no tiene historial completo
    s_home = stats.get(team_home, {'goals_sc': 1.5, 'goals_co': 1.0, 'elo': 1500})
    s_away = stats.get(team_away, {'goals_sc': 1.2, 'goals_co': 1.1, 'elo': 1500})
    
    # Calcular la expectativa de goles usando sus promedios cruzados
    # Goles esperados de Home = Goles que anota Home * Goles que recibe Away
    # Agregamos una ligera ventaja neutral basada en el Elo histórico si aplica
    elo_diff = s_home['elo'] - s_away['elo']
    elo_adjustment = elo_diff / 1000.0
    
    lambda_home = max(0.5, (s_home['goals_sc'] + s_away['goals_co']) / 2.0 + elo_adjustment)
    lambda_away = max(0.5, (s_away['goals_sc'] + s_home['goals_co']) / 2.0 - elo_adjustment)
    
    max_goals = 6
    score_matrix = np.zeros((max_goals, max_goals))
    
    # Construir la matriz de Poisson
    for i in range(max_goals): # Goles Home
        for j in range(max_goals): # Goles Away
            prob_home = poisson.pmf(i, lambda_home)
            prob_away = poisson.pmf(j, lambda_away)
            score_matrix[i, j] = prob_home * prob_away
            
    # Calcular probabilidades generales agrupadas
    prob_home_win = np.sum(np.tril(score_matrix, -1))
    prob_away_win = np.sum(np.triu(score_matrix, 1))
    prob_draw = np.sum(np.diag(score_matrix))
    
    print(f"\n📊 --- ANÁLISIS PROBABILÍSTICO: {team_home} vs {team_away} ---")
    print(f"⚽ Goles esperados de {team_home}: {lambda_home:.2f}")
    print(f"⚽ Goles esperados de {team_away}: {lambda_away:.2f}\n")
    
    print(f"🟢 Probabilidad {team_home} gana: {prob_home_win * 100:.2f}%")
    print(f"⚪ Probabilidad Empate: {prob_draw * 100:.2f}%")
    print(f"🔵 Probabilidad {team_away} gana: {prob_away_win * 100:.2f}%")
    
    # Encontrar los 3 scores más probables
    scores_flat = []
    for i in range(max_goals):
        for j in range(max_goals):
            scores_flat.append(((i, j), score_matrix[i, j]))
            
    top_scores = sorted(scores_flat, key=lambda x: x[1], reverse=True)[:3]
    
    print(f"\n🎯 TOP 3 SCORES EXACTOS MÁS PROBABLES:")
    for idx, (score, prob) in enumerate(top_scores):
        print(f"   {idx+1}. Marcador {score[0]}-{score[1]} ➔ Probabilidad: {prob*100:.2f}%")
        
    # --- VISUALIZACIÓN: MATRIZ DE CALOR CLEAN & MINIMALIST ---
    plt.figure(figsize=(8, 6))
    plt.imshow(score_matrix, cmap='Blues', origin='lower')
    
    # Anotar los porcentajes dentro de cada cuadrante de la matriz
    for i in range(max_goals):
        for j in range(max_goals):
            plt.text(j, i, f"{score_matrix[i, j]*100:.1f}%", ha='center', va='center',
                     color='white' if score_matrix[i, j] > 0.06 else 'black', fontsize=9)
            
    plt.title(f"Matriz de Probabilidad de Score Exacto\n{team_home} vs {team_away}", fontsize=12, pad=15)
    plt.xlabel(f"Goles de {team_away}", fontsize=10)
    plt.ylabel(f"Goles de {team_home}", fontsize=10)
    plt.xticks(range(max_goals))
    plt.yticks(range(max_goals))
    
    # Estética minimalista sin bordes pesados
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
        
    os.makedirs("output", exist_ok=True)
    plt.tight_layout()
    plt.savefig(os.path.join("output", f"probabilidad_score_{team_home}_vs_{team_away}.png"), dpi=300)
    plt.close()
    print(f"\n🎨 Gráfico guardado en: output/probabilidad_score_{team_home}_vs_{team_away}.png\n")

if __name__ == "__main__":
    try:
        # Instalar scipy si hace falta
        os.system("pip install scipy --quiet")
        stats = get_team_stats()
        
        # Consultamos el partido específico que pediste
        predict_score_probability("Brazil", "Morocco", stats)
    except Exception as e:
        print(f"❌ Error: {e}")