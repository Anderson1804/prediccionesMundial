import pandas as pd
import numpy as np
from .lambda_calculator import LambdaCalculator

class TournamentSimulator:
    def __init__(self, df_groups):
        # df_groups ya debe venir traducido y limpio desde el ETL
        self.df_groups = df_groups
        
    def _simulate_match_90min(self, team_a, team_b):
        """Simula un partido usando el LambdaCalculator y distribución de Poisson."""
        calc = LambdaCalculator(team_a, team_b)
        # Obtenemos los lambdas de goles esperados
        lambda_a, lambda_b, _, _ = calc.calculate_lambdas()
        
        # Generamos los goles aleatorios usando Poisson
        goles_a = np.random.poisson(lambda_a)
        goles_b = np.random.poisson(lambda_b)
        
        return goles_a, goles_b

    def _simulate_knockout_match(self, team_a, team_b):
        """Simula partidos de eliminación directa (fase playoffs) donde DEBE haber un ganador."""
        goles_a, goles_b = self._simulate_match_90min(team_a, team_b)
        
        if goles_a != goles_b:
            return team_a if goles_a > goles_b else team_b
        
        # Desempate estocástico simple (Simulación de penales/tiempo extra 50/50 o por ligera ventaja)
        # Puedes meterle más adelante peso por ranking ELO si deseas afinarlo más con el jurado
        return np.random.choice([team_a, team_b])

    def simulate_group_stage(self):
        """Simula toda la fase de grupos y devuelve los clasificados."""
        # Diccionario para guardar puntos de cada equipo en esta iteración
        puntos = {team: 0 for team in self.df_groups['team'].unique()}
        
        # Iteramos grupo por grupo (Cada grupo tiene 4 equipos)
        for grupo, df_g in self.df_groups.groupby('group'):
            equipos = df_g['team'].tolist()
            # Todos contra todos en el grupo (3 partidos por equipo)
            for i in range(len(equipos)):
                for j in range(i + 1, len(equipos)):
                    team_1 = equipos[i]
                    team_2 = equipos[j]
                    
                    g1, g2 = self._simulate_match_90min(team_1, team_2)
                    
                    if g1 > g2:
                        puntos[team_1] += 3
                    elif g2 > g1:
                        puntos[team_2] += 3
                    else:
                        puntos[team_1] += 1
                        puntos[team_2] += 1
                        
        # Clasificamos a los 2 mejores de cada grupo de forma simplificada por puntos
        # (Para el alcance de la tesis, los top 32 avanzan directo)
        df_posiciones = pd.DataFrame(puntos.items(), columns=['team', 'puntos'])
        df_posiciones = df_posiciones.merge(self.df_groups[['team', 'group']], on='team')
        
        # Clasificar top 2 por grupo
        clasificados = []
        for grupo, df_g in df_posiciones.groupby('group'):
            top_2 = df_g.sort_values(by='puntos', ascending=False).head(2)['team'].tolist()
            clasificados.extend(top_2)
            
        # Para completar los 32 de la llave (Mundial 2026 tiene 12 grupos = 24 clasificados directos)
        # Los 8 mejores terceros se suman agarrando los que tengan más puntos de los restantes
        eliminados = df_posiciones[~df_posiciones['team'].isin(clasificados)]
        mejores_terceros = eliminados.sort_values(by='puntos', ascending=False).head(8)['team'].tolist()
        
        clasificados.extend(mejores_terceros)
        return clasificados  # Lista con los 32 sobrevivientes

    def run_full_tournament(self):
        """Simula el torneo completo desde grupos hasta la final y devuelve al Campeón."""
        # 1. Fase de Grupos
        playoffs_32 = self.simulate_group_stage()
        
        # 2. Dieciseisavos de Final (32 -> 16)
        playoffs_16 = []
        for i in range(0, len(playoffs_32), 2):
            ganador = self._simulate_knockout_match(playoffs_32[i], playoffs_32[i+1])
            playoffs_16.append(ganador)
            
        # 3. Octavos de Final (16 -> 8)
        playoffs_8 = []
        for i in range(0, len(playoffs_16), 2):
            ganador = self._simulate_knockout_match(playoffs_16[i], playoffs_16[i+1])
            playoffs_8.append(ganador)
            
        # 4. Cuartos de Final (8 -> 4)
        playoffs_4 = []
        for i in range(0, len(playoffs_8), 2):
            ganador = self._simulate_knockout_match(playoffs_8[i], playoffs_8[i+1])
            playoffs_4.append(ganador)
            
        # 5. Semifinal (4 -> 2)
        finalistas = []
        for i in range(0, len(playoffs_4), 2):
            ganador = self._simulate_knockout_match(playoffs_4[i], playoffs_4[i+1])
            finalistas.append(ganador)
            
        # 6. Gran Final
        campeon = self._simulate_knockout_match(finalistas[0], finalistas[1])
        return campeon