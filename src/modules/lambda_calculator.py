import os
import numpy as np
import pandas as pd
from . import config
from .data_loader import DataLoader
from .hierarchy_generator import HierarchyGenerator

class LambdaCalculator:
    def __init__(self, team_home, team_away):
        self.team_home = team_home  # Nombre del equipo local
        self.team_away = team_away  # Nombre del equipo visitante
        
        self.df_results = DataLoader.get_new_results()
        self.df_goalscores = DataLoader.get_goalscores()
        self.df_rankings = DataLoader.get_fifa_rankings()
        self.df_players = DataLoader.get_jugadores_valores()

    def _get_historical_stats(self, team):
        """
        Calcula promedios de goles anotados y recibidos ponderados por torneo y nivel del rival.
        """
        # Filtrar partidos en los que participó el equipo
        team_matches = self.df_results[(self.df_results['home_team'] == team) | (self.df_results['away_team'] == team)].copy()
        team_matches = team_matches.sort_values(by='date', ascending=False).head(config.HISTORIC_MATCH_LIMIT)
        
        if team_matches.empty:
            return 1.35, 1.15

        pesos_torneo = {
            "FIFA World Cup": 1.5, "Copa América": 1.3, "UEFA Euro": 1.3,
            "FIFA World Cup qualification": 1.2, "UEFA Nations League": 1.0, "Friendly": 0.6
        }

        goles_anotados_ponderados = []
        goles_recibidos_ponderados = []

        dict_elo = dict(zip(self.df_rankings['team'], self.df_rankings['elo']))
        elo_base_mundial = 1500.0

        for _, row in team_matches.iterrows():
            try:
                torneo = row['tournament']
                w_torneo = pesos_torneo.get(torneo, 1.0)

                h_sc = float(row['home_score'])
                a_sc = float(row['away_score'])

                if row['home_team'] == team:
                    rival = row['away_team']
                    goles_puros_gf = h_sc
                    goles_puros_gc = a_sc
                else:
                    rival = row['home_team']
                    goles_puros_gf = a_sc
                    goles_puros_gc = h_sc

                elo_rival = float(dict_elo.get(rival.strip(), elo_base_mundial))

                factor_dificultad_ofensiva = elo_rival / 1600.0
                factor_dificultad_defensiva = 1600.0 / elo_rival

                goles_anotados_ponderados.append(goles_puros_gf * w_torneo * factor_dificultad_ofensiva)
                goles_recibidos_ponderados.append(goles_puros_gc * w_torneo * factor_dificultad_defensiva)
            except Exception:
                continue

        avg_gf = np.mean(goles_anotados_ponderados) if goles_anotados_ponderados else 1.35
        avg_gc = np.mean(goles_recibidos_ponderados) if goles_recibidos_ponderados else 1.15
        
        if np.isnan(avg_gf): avg_gf = 1.35
        if np.isnan(avg_gc): avg_gc = 1.15

        return float(avg_gf), float(avg_gc)

    def calculate_lambdas(self, titulares_manual_home=None, titulares_manual_away=None):
        """
        Calcula las expectativas de goles (lambda) ajustando por valor de plantilla,
        jerarquía histórica y factor de localía.
        """
        avg_gf_home, avg_gc_home = self._get_historical_stats(self.team_home)
        avg_gf_away, avg_gc_away = self._get_historical_stats(self.team_away)
        
        stats_home = {"gf": avg_gf_home, "gc": avg_gc_home}
        stats_away = {"gf": avg_gf_away, "gc": avg_gc_away}

        # Goles anotados según registro histórico
        goles_pool_home = self.df_goalscores[(self.df_goalscores['team'] == self.team_home) & (self.df_goalscores['own_goal'] == False)]
        goles_pool_away = self.df_goalscores[(self.df_goalscores['team'] == self.team_away) & (self.df_goalscores['own_goal'] == False)]

        if titulares_manual_home and len(titulares_manual_home) > 0:
            goles_tit_home = goles_pool_home[goles_pool_home['scorer'].isin(titulares_manual_home)].shape[0]
        else:
            goles_tit_home = goles_pool_home['scorer'].value_counts().head(11).sum()

        if titulares_manual_away and len(titulares_manual_away) > 0:
            goles_tit_away = goles_pool_away[goles_pool_away['scorer'].isin(titulares_manual_away)].shape[0]
        else:
            goles_tit_away = goles_pool_away['scorer'].value_counts().head(11).sum()

        total_goles_h = max(1, goles_pool_home.shape[0])
        total_goles_a = max(1, goles_pool_away.shape[0])
        
        f_ofensivo_home = 1.0 + np.sqrt(goles_tit_home / total_goles_h) * 0.25
        f_ofensivo_away = 1.0 + np.sqrt(goles_tit_away / total_goles_a) * 0.25

        # Valor de mercado de los jugadores
        pool_home = self.df_players[self.df_players['team'] == self.team_home]
        pool_away = self.df_players[self.df_players['team'] == self.team_away]
        
        if titulares_manual_home and len(titulares_manual_home) > 0:
            valores_tit_home = pool_home[pool_home['player'].isin(titulares_manual_home)]['value'].tolist()
        else:
            valores_tit_home = pool_home.sort_values(by='value', ascending=False).head(11)['value'].tolist()
            
        if titulares_manual_away and len(titulares_manual_away) > 0:
            valores_tit_away = pool_away[pool_away['player'].isin(titulares_manual_away)]['value'].tolist()
        else:
            valores_tit_away = pool_away.sort_values(by='value', ascending=False).head(11)['value'].tolist()

        if not valores_tit_home: valores_tit_home = [1.0] * 11
        if not valores_tit_away: valores_tit_away = [1.0] * 11

        cv_home = np.std(valores_tit_home) / (np.mean(valores_tit_home) if np.mean(valores_tit_home) > 0 else 1)
        cv_away = np.std(valores_tit_away) / (np.mean(valores_tit_away) if np.mean(valores_tit_away) > 0 else 1)
        
        vulnerabilidad_home = 1.0 - (min(1.5, cv_home) * 0.05)
        vulnerabilidad_away = 1.0 - (min(1.5, cv_away) * 0.05)

        impacto_financiero_home = np.log10(sum(valores_tit_home) + 1) * vulnerabilidad_home
        impacto_financiero_away = np.log10(sum(valores_tit_away) + 1) * vulnerabilidad_away

        # Factor de jerarquía histórica del equipo
        f_hierarchy_home = HierarchyGenerator.get_factor(self.team_home, self.df_rankings)
        f_hierarchy_away = HierarchyGenerator.get_factor(self.team_away, self.df_rankings)
        
        # Estimación base de goles esperados
        base_lambda_home = np.sqrt(avg_gf_home * (avg_gc_away + 0.5))
        base_lambda_away = np.sqrt(avg_gf_away * (avg_gc_home + 0.5))

        ratio_financiero = 1.0 + (np.log10(impacto_financiero_home / impacto_financiero_away) if impacto_financiero_away > 0 else 0) * 0.3
        ratio_jerarquia = 1.0 + np.log(f_hierarchy_home / f_hierarchy_away) * 0.4
        ratio_jugadores = f_ofensivo_home / f_ofensivo_away

        # Ajuste por localía para los países anfitriones del torneo
        anfitriones = ["México", "Canadá", "Estados Unidos"]
        factor_localia_ataque = 1.12
        factor_localia_defensa = 0.90

        lambda_home = base_lambda_home * ratio_jugadores * ratio_financiero * ratio_jerarquia
        lambda_away = base_lambda_away * (1.0 / ratio_jugadores) * (1.0 / ratio_financiero) * (1.0 / ratio_jerarquia)

        if self.team_home in anfitriones:
            lambda_home *= factor_localia_ataque
            lambda_away *= factor_localia_defensa
        elif self.team_away in anfitriones:
            lambda_home *= 0.95
            lambda_away *= 1.05
        # =====================================================================

        lambda_home = max(0.25, min(4.8, lambda_home))
        lambda_away = max(0.25, min(4.8, lambda_away))
        
        return round(float(lambda_home), 2), round(float(lambda_away), 2), stats_home, stats_away