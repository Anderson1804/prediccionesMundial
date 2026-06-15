import os
import pandas as pd
from . import config

class HierarchyGenerator:
    _instance = None
    _market_values = {}

    @classmethod
    def initialize(cls):
        """Carga el CSV de valores de mercado en memoria una sola vez (Patrón Singleton)"""
        if not cls._market_values:
            file_path = os.path.join(config.DATA_DIR, "market_values.csv")
            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path)
                    # 💡 dict(zip(...)) corregido y ultra rápido
                    cls._market_values = dict(zip(df['team'], df['market_value']))
                except Exception as e:
                    print(f"⚠️ Advertencia al leer market_values.csv: {e}. Usando valores por defecto.")
            else:
                print("⚠️ No se encontró data/market_values.csv. Se usarán jerarquías por defecto.")

    @classmethod
    def get_factor(cls, team, df_rankings):
        """
        Calcula dinámicamente la jerarquía competitiva cruzando el valor financiero 
        de la plantilla con su posición en el Ranking FIFA.
        """
        cls.initialize()
        
        try:
            # 1. Componente Ranking FIFA: Escala inversa (Puesto 1 es ~1.0, Puesto 85+ tiende a 0.1)
            row_rank = df_rankings[df_rankings['team'] == team]
            rank = int(row_rank['fifa_rank'].values[0]) if not row_rank.empty else 85
            rank_score = max(0.1, 1.0 - (rank / 100.0))
            
            # 2. Componente Financiero: Escala proporcional respecto al techo de tu CSV (France ~1520M)
            market_val = float(cls._market_values.get(team, 40.0)) # 40M por defecto si es selección menor
            max_market_value = 1520.0 
            market_score = min(1.0, market_val / max_market_value)
            
            # 3. Fusión Ponderada: 60% peso financiero (calidad individual) + 40% ranking (consistencia)
            base_score = (0.60 * market_score) + (0.40 * rank_score)
            
            # 4. Mapeo a la escala de Lambdas de tu modelo (Oscila estrictamente entre 0.50 y 1.35)
            final_factor = 0.50 + (base_score * 0.85)
            return round(final_factor, 3)
            
        except Exception:
            return 0.80 # Factor seguro de contingencia