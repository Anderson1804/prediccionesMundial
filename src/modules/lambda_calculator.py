import os
import numpy as np
import pandas as pd
from . import config
from .hierarchy_generator import HierarchyGenerator

class LambdaCalculator:
    def __init__(self, team_home, team_away):
        self.team_home = team_home
        self.team_away = team_away
        self.df_rankings = self._load_rankings()

    def _load_rankings(self):
        """Carga el archivo de rankings/ELO desde el directorio de datos"""
        file_path = os.path.join(config.DATA_DIR, "rankings.csv")
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return pd.DataFrame(columns=['team', 'fifa_rank', 'elo'])

    def _get_team_elo(self, team):
        """Busca el ELO del equipo, si no existe devuelve un ELO base de 1500"""
        if self.df_rankings.empty or 'elo' not in self.df_rankings.columns:
            return 1500.0
        row = self.df_rankings[self.df_rankings['team'] == team]
        return float(row['elo'].values[0]) if not row.empty else 1500.0

    def calculate_lambdas(self):
        """
        🚀 EXPERIMENTO: Peso 90/10 (Once Titular dominante) y 
        Cero sesgo de localía (Simulación perfecta de campo neutral de Mundial).
        """
        # 💡 EXTRACCIÓN DETALLADA JUGADOR POR JUGADOR
        file_players = os.path.join(config.DATA_DIR, "jugadores_valores.csv")
        df_players = pd.read_csv(file_players)
        
        # Filtrar futbolistas de cada selección
        players_home = df_players[df_players['team'] == self.team_home].copy()
        players_away = df_players[df_players['team'] == self.team_away].copy()
        
        # Extraer listas ordenadas de mayor a menor
        valores_home = sorted(players_home['value'].tolist(), reverse=True)
        valores_away = sorted(players_away['value'].tolist(), reverse=True)
        
        # Respaldos de seguridad por si las listas son cortas
        while len(valores_home) < 26: valores_home.append(0.5)
        while len(valores_away) < 26: valores_away.append(0.5)
            
        # Segmentación exacta
        top11_home = sum(valores_home[:11])
        bench_home = sum(valores_home[11:26])
        top11_away = sum(valores_away[:11])
        bench_away = sum(valores_away[11:26])
        
        # 🧠 EVALUACIÓN CUALITATIVA DE CALIDAD POR INDIVIDUALIDADES
        titulares_home = valores_home[:11]
        titulares_away = valores_away[:11]
        
        # Medimos el Coeficiente de Variación (Dispersión de calidad en el Once Titular)
        cv_home = np.std(titulares_home) / (np.mean(titulares_home) if np.mean(titulares_home) > 0 else 1)
        cv_away = np.std(titulares_away) / (np.mean(titulares_away) if np.mean(titulares_away) > 0 else 1)
        
        # Factor táctico: Si la calidad está repartida homogéneamente el equipo es robusto. 
        # Si un solo jugador acapara todo el dinero, el equipo sufre de "dependencia táctica".
        vulnerabilidad_home = 1.0 - (min(0.25, cv_home) * 0.4)
        vulnerabilidad_away = 1.0 - (min(0.25, cv_away) * 0.4)
        
        # 🌟 Impacto en campo con balance 90/10 + Multiplicador Cualitativo de Jugadores Real
        impact_home = ((0.90 * top11_home) + (0.10 * bench_home)) * vulnerabilidad_home
        impact_away = ((0.90 * top11_away) + (0.10 * bench_away)) * vulnerabilidad_away
        
        # 🧠 CONEXIÓN CON MÉTRICAS DE ENTORNO (Mapeo de Densidad de Goles)
        factor_home = HierarchyGenerator.get_factor(self.team_home, self.df_rankings)
        factor_away = HierarchyGenerator.get_factor(self.team_away, self.df_rankings)
        elo_home = self._get_team_elo(self.team_home)
        elo_away = self._get_team_elo(self.team_away)
        
        goal_trend_modifier = 1.25
        
        density_home = factor_home * (elo_home / 1000.0) * np.log10(impact_home) * goal_trend_modifier
        density_away = factor_away * (elo_away / 1000.0) * np.log10(impact_away) * goal_trend_modifier
        
        # 🏟️ CALCULADORA DE LAMBDAS EN CAMPO NEUTRAL (Simbología Simétrica 1.50)
        lambda_home = max(0.4, (density_home / max(1.0, density_away)) * 1.50)
        lambda_away = max(0.4, (density_away / max(1.0, density_home)) * 1.50)
        
        return round(lambda_home, 2), round(lambda_away, 2)