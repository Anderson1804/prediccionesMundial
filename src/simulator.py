import os
import pandas as pd
import joblib
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
model_path = os.path.join("models", "world_cup_predictor.joblib")
if not os.path.exists(model_path):
    raise FileNotFoundError("❌ Primero debes entrenar el modelo con train_model.py")

model = joblib.load(model_path)

# Grupos Oficiales de la Copa Mundial de la FIFA 2026 (48 selecciones)
WORLD_CUP_GROUPS = {
    "Grupo A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "Grupo B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "Grupo C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "Grupo D": ["United States", "Paraguay", "Australia", "Turkey"],
    "Grupo E": ["Germany", "Curacao", "Ivory Coast", "Ecuador"],
    "Grupo F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "Grupo G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "Grupo H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "Grupo I": ["France", "Senegal", "Iraq", "Norway"],
    "Grupo J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "Grupo K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "Grupo L": ["England", "Croatia", "Ghana", "Panama"]
}

def get_team_stats():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    local_matches = os.path.join("data", "matches_with_elo.csv")
    with open(local_matches, "wb") as f:
        res = supabase.storage.from_("datasets").download("matches_with_elo.csv")
        f.write(res)
        
    df_matches = pd.read_csv(local_matches)
    df_matches['match_date'] = pd.to_datetime(df_matches['match_date'])
    df_matches = df_matches.sort_values(by='match_date')
    
    stats_dict = {}
    for _, row in df_matches.iterrows():
        stats_dict[row['home_team']] = {
            'elo': row['home_elo_before'], 'goals_sc': row['home_goals_scored_avg'],
            'goals_co': row['home_goals_conceded_avg'], 'form': row['home_form_avg']
        }
        stats_dict[row['away_team']] = {
            'elo': row['away_elo_before'], 'goals_sc': row['away_goals_scored_avg'],
            'goals_co': row['away_goals_conceded_avg'], 'form': row['away_form_avg']
        }
    return stats_dict

def predict_match_outcome(team_a, team_b, stats, weight=4.0):
    stats_a = stats.get(team_a, {'elo': 1500.0, 'goals_sc': 1.0, 'goals_co': 1.0, 'form': 1.0})
    stats_b = stats.get(team_b, {'elo': 1500.0, 'goals_sc': 1.0, 'goals_co': 1.0, 'form': 1.0})
    
    elo_diff = stats_a['elo'] - stats_b['elo']
    goals_sc_diff = stats_a['goals_sc'] - stats_b['goals_sc']
    goals_co_diff = stats_a['goals_co'] - stats_b['goals_co']
    form_diff = stats_a['form'] - stats_b['form']
    is_neutral = 1 
    
    features = pd.DataFrame(
        [[elo_diff, is_neutral, goals_sc_diff, goals_co_diff, form_diff, weight]],
        columns=['elo_difference', 'is_neutral', 'goals_scored_diff', 'goals_conceded_diff', 'form_difference', 'tournament_weight']
    )
    
    prediction = model.predict(features)[0]
    return prediction

def simulate_groups(stats):
    print("🏆 --- SIMULANDO LA FASE DE GRUPOS DEL MUNDIAL 2026 (48 EQUIPOS) ---")
    direct_classified = []
    all_third_places = []
    
    for group_name, teams in WORLD_CUP_GROUPS.items():
        points = {team: 0 for team in teams}
        gd = {team: 0 for team in teams} # Goal Difference simulada para desempates básicos
        
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                t1, t2 = teams[i], teams[j]
                res = predict_match_outcome(t1, t2, stats, weight=4.0)
                
                if res == 2:   
                    points[t1] += 3; gd[t1] += 1; gd[t2] -= 1
                elif res == 0: 
                    points[t2] += 3; gd[t2] += 1; gd[t1] -= 1
                else:          
                    points[t1] += 1; points[t2] += 1
                    
        # Ordenar grupo por puntos y luego por diferencia de goles simulada
        sorted_group = sorted(points.items(), key=lambda x: (x[1], gd[x[0]]), reverse=True)
        
        # Guardar 1ro y 2do lugar
        direct_classified.append(sorted_group[0][0])
        direct_classified.append(sorted_group[1][0])
        
        # Guardar el 3er lugar para evaluar mejores terceros
        all_third_places.append({'team': sorted_group[2][0], 'pts': sorted_group[2][1], 'gd': gd[sorted_group[2][0]]})
        
        print(f"\n📌 {group_name} posiciones finales:")
        for idx, (team, pts) in enumerate(sorted_group):
            icon = "✅" if idx < 2 else ("🔶" if idx == 2 else "❌")
            print(f"   {idx+1}. {team}: {pts} pts {icon}")
            
    # Filtrar los 8 mejores terceros
    sorted_thirds = sorted(all_third_places, key=lambda x: (x['pts'], x['gd']), reverse=True)
    best_thirds = [x['team'] for x in sorted_thirds[:8]]
    
    print("\n🔶 --- 8 MEJORES TERCEROS CLASIFICADOS ---")
    for idx, t in enumerate(sorted_thirds[:8]):
        print(f"   {idx+1}. {t['team']} ({t['pts']} pts)")
        
    return direct_classified + best_thirds

def simulate_knockout_stage(qualified_teams, stats):
    def play_elimination_match(team_a, team_b):
        res = predict_match_outcome(team_a, team_b, stats, weight=4.0)
        if res == 2: return team_a
        elif res == 0: return team_b
        else:
            elo_a = stats.get(team_a, {'elo': 1500})['elo']
            elo_b = stats.get(team_b, {'elo': 1500})['elo']
            return team_a if elo_a >= elo_b else team_b

    print("\n🔥 --- SIMULANDO LLAVES DE ELIMINACIÓN DIRECTA ---")
    
    # 1. DIECISEISAVOS DE FINAL (32 equipos -> 16 llaves)
    print("\n⚽ [DIECISEISAVOS DE FINAL - ROUND OF 32]")
    round_of_16_teams = []
    for i in range(0, len(qualified_teams), 2):
        t1 = qualified_teams[i]
        t2 = qualified_teams[i+1]
        winner = play_elimination_match(t1, t2)
        print(f"   {t1} vs {t2} ➔ Ganador: {winner}")
        round_of_16_teams.append(winner)
        
    # 2. OCTAVOS DE FINAL (16 equipos -> 8 llaves)
    print("\n⚽ [OCTAVOS DE FINAL]")
    cuartos_teams = []
    for i in range(0, len(round_of_16_teams), 2):
        t1, t2 = round_of_16_teams[i], round_of_16_teams[i+1]
        winner = play_elimination_match(t1, t2)
        print(f"   {t1} vs {t2} ➔ Ganador: {winner}")
        cuartos_teams.append(winner)
        
    # 3. CUARTOS DE FINAL (8 equipos -> 4 llaves)
    print("\n⚽ [CUARTOS DE FINAL]")
    semis_teams = []
    for i in range(0, len(cuartos_teams), 2):
        t1, t2 = cuartos_teams[i], cuartos_teams[i+1]
        winner = play_elimination_match(t1, t2)
        print(f"   {t1} vs {t2} ➔ Ganador: {winner}")
        semis_teams.append(winner)
        
    # 4. SEMIFINALES (4 equipos -> 2 llaves)
    print("\n⚽ [SEMIFINALES]")
    finalists = []
    for i in range(0, len(semis_teams), 2):
        t1, t2 = semis_teams[i], semis_teams[i+1]
        winner = play_elimination_match(t1, t2)
        print(f"   {t1} vs {t2} ➔ Ganador: {winner}")
        finalists.append(winner)
        
    # 5. GRAN FINAL
    print("\n👑 [GRAN FINAL DEL MUNDIAL 2026]")
    champion = play_elimination_match(finalists[0], finalists[1])
    print(f"   🏆 {finalists[0]} vs {finalists[1]} ➔ ¡CAMPEÓN DEL MUNDO: {champion}! 🏆\n")

if __name__ == "__main__":
    try:
        stats = get_team_stats()
        qualified = simulate_groups(stats)
        simulate_knockout_stage(qualified, stats)
        print("=======================================================")
        input("🏁 Presiona ENTER para finalizar la simulación...")
        print("=======================================================")
    except Exception as e:
        print(f"❌ Error en la simulación: {e}")
        input()