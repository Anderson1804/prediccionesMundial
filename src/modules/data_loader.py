import os
import pandas as pd
from . import config

class DataLoader:
    @staticmethod
    def get_new_results():
        """Carga los resultados históricos procesados y limpios."""
        path = os.path.join(config.DATA_DIR, "clean_results.csv")
        if not os.path.exists(path):
            raise FileNotFoundError("❌ No se encuentra 'clean_results.csv'. Ejecuta primero python src/clean_datasets.py")
        return pd.read_csv(path, encoding='utf-8')

    @staticmethod
    def get_goalscores():
        """Carga el registro de goles históricos procesado."""
        path = os.path.join(config.DATA_DIR, "clean_goalscores.csv")
        if not os.path.exists(path):
            raise FileNotFoundError("❌ No se encuentra 'clean_goalscores.csv'. Ejecuta primero python src/clean_datasets.py")
        return pd.read_csv(path, encoding='utf-8')

    @staticmethod
    def get_fifa_rankings():
        """Carga el ranking FIFA y Elo unificado."""
        path = os.path.join(config.DATA_DIR, "clean_rankings.csv")
        if not os.path.exists(path):
            raise FileNotFoundError("❌ No se encuentra 'clean_rankings.csv'. Ejecuta primero python src/clean_datasets.py")
        return pd.read_csv(path, encoding='utf-8')

    @staticmethod
    def get_jugadores_valores():
        """Carga los valores de mercado de las plantillas."""
        path = os.path.join(config.DATA_DIR, "clean_jugadores_valores.csv")
        if not os.path.exists(path):
            raise FileNotFoundError("❌ No se encuentra 'clean_jugadores_valores.csv'. Ejecuta primero python src/clean_datasets.py")
        return pd.read_csv(path, encoding='utf-8')