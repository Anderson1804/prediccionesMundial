import pandas as pd
import numpy as np

class HierarchyGenerator:
    @classmethod
    def get_factor(cls, team, df_rankings):
        """
        Calcula un factor de fuerza basado en Ranking FIFA y puntuación Elo.
        Retorna un factor multiplicador.
        """
        try:
            row = df_rankings[df_rankings['team'] == team]
            if row.empty:
                return 1.0
            
            rank = int(row['fifa_rank'].values[0]) if 'fifa_rank' in row.columns else 50
            elo = float(row['elo'].values[0]) if 'elo' in row.columns else 1500.0
            
            # Normalizar ranking y Elo para obtener un puntaje unificado
            rank_score = max(0.1, 1.0 - (rank / 100.0))
            elo_score = elo / 1500.0
            
            return round((0.40 * rank_score) + (0.60 * elo_score), 3)
        except Exception:
            return 1.0