import os
import numpy as np
import pandas as pd
from modules import config
from modules.lambda_calculator import LambdaCalculator

class TournamentSimulator:
    def __init__(self):
        self.groups_path = os.path.join(config.DATA_DIR, "world_cup_groups.csv")
        if not os.path.exists(self.groups_path):
            raise FileNotFoundError("❌ No se encuentra data/world_cup_groups.csv. Por favor, créalo primero.")
        self.df_groups = pd.read_csv(self.groups_path)

    def _simulate_single_match(self, home, away):
        """Simula un único partido de 90 minutos usando el motor Lambda de Poisson"""
        calculator = LambdaCalculator(home, away)
        lambda_home, lambda_away = calculator.calculate_lambdas()
        
        # Generamos un marcador aleatorio basado en los Lambdas calculados
        goals_home = np.random.poisson(lambda_home)
        goals_away = np.random.poisson(lambda_away)
        return goals_home, goals_away

    def _simulate_group_stage(self):
        """Simula todos los partidos de la fase de grupos y calcula clasificados"""
        classified_teams = []
        grouped = self.df_groups.groupby('group')
        
        for group_name, group_df in grouped:
            teams = group_df['team'].tolist()
            # Inicializamos la tabla de posiciones del grupo
            stats = {team: {"points": 0, "gf": 0, "ga": 0, "gd": 0} for team in teams}
            
            # Formato todos contra todos (Round Robin) dentro del grupo
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    team_a = teams[i]
                    team_b = teams[j]
                    
                    # Simulación del partido de fase de grupos
                    ga, gb = self._simulate_single_match(team_a, team_b)
                    
                    # Asignación de puntos y goles
                    stats[team_a]["gf"] += ga
                    stats[team_a]["ga"] += gb
                    stats[team_b]["gf"] += gb
                    stats[team_b]["ga"] += ga
                    
                    if ga > gb:
                        stats[team_a]["points"] += 3
                    elif gb > ga:
                        stats[team_b]["points"] += 3
                    else:
                        stats[team_a]["points"] += 1
                        stats[team_b]["points"] += 1
            
            # Calcular diferencia de goles (GD)
            for team in stats:
                stats[team]["gd"] = stats[team]["gf"] - stats[team]["ga"]
                
            # Ordenar la tabla del grupo por Puntos, luego por Diferencia de Goles y Goles a Favor
            sorted_table = sorted(
                stats.items(), 
                key=lambda x: (x[1]["points"], x[1]["gd"], x[1]["gf"]), 
                reverse=True
            )
            
            # Clasifican los 2 primeros del grupo de forma directa
            classified_teams.append(sorted_table[0][0])
            classified_teams.append(sorted_table[1][0])
            
        return classified_teams

    def _simulate_knockout_stage(self, teams):
        """Simula las llaves de eliminación directa incorporando penales estocásticos"""
        current_round = teams.copy()
        
        while len(current_round) > 1:
            next_round = []
            for i in range(0, len(current_round), 2):
                if i + 1 >= len(current_round):
                    next_round.append(current_round[i])
                    break
                    
                team_home = current_round[i]
                team_away = current_round[i+1]
                
                ga, gb = self._simulate_single_match(team_home, team_away)
                
                if ga == gb:
                    # --- PENALES ESTOCÁSTICOS CON PESO DE JERARQUÍA ---
                    calculator = LambdaCalculator(team_home, team_away)
                    lh, la = calculator.calculate_lambdas()
                    
                    # El azar influye usando Monte Carlo real, pero ponderado por su rendimiento
                    prob_home_penal = lh / (lh + la)
                    
                    if np.random.rand() < prob_home_penal:
                        winner = team_home
                    else:
                        winner = team_away
                else:
                    winner = team_home if ga > gb else team_away
                    
                next_round.append(winner)
            current_round = next_round
            
        return current_round[0]

    def run_tournament_monte_carlo(self, num_tournaments=1000):
        """Ejecuta la simulación macro del torneo completo mediante Monte Carlo"""
        print(f"🎲 Iniciando simulación estocástica de {num_tournaments} Mundiales completos...")
        champions_registry = {}
        
        for i in range(1, num_tournaments + 1):
            if i % 100 == 0:
                print(f"🔄 Torneos procesados: {i}/{num_tournaments}...")
                
            # 1. Simular Fase de Grupos
            playoff_teams = self._simulate_group_stage()
            
            # 2. Simular Fases de Eliminación Directa
            champion = self._simulate_knockout_stage(playoff_teams)
            
            # 3. Registrar al campeón de esta iteración
            champions_registry[champion] = champions_registry.get(champion, 0) + 1
            
        # Calcular probabilidades porcentuales finales
        df_champs = pd.DataFrame(list(champions_registry.items()), columns=['Selección', 'Copas'])
        df_champs['Probabilidad_Campeón'] = (df_champs['Copas'] / num_tournaments) * 100
        df_champs = df_champs.sort_values(by='Probabilidad_Campeón', ascending=False).reset_index(drop=True)
        
        print("\n" + "═"*55)
        print("🏆   REPORTE PROBABILÍSTICO: CANDIDATOS AL TÍTULO MUNDIAL   🏆")
        print("═"*55)
        for idx, row in df_champs.head(10).iterrows():
            print(f" {idx+1:>2}. {row['Selección']:<18} ➔ Probabilidad: {row['Probabilidad_Campeón']:>6.2f}% ({row['Copas']} títulos)")
        print("═"*55 + "\n")
        
        return df_champs

if __name__ == "__main__":
    simulator = TournamentSimulator()
    # Ejecutamos 1000 iteraciones completas para estabilizar la varianza del modelo macro
    simulator.run_tournament_monte_carlo(num_tournaments=1000)