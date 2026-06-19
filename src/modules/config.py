import os

# Control de rutas del proyecto
MODULES_DIR = os.path.dirname(os.path.abspath(__file__)) # src/modules
SRC_DIR = os.path.dirname(MODULES_DIR)                  # src
BASE_DIR = os.path.dirname(SRC_DIR)                     # raíz del proyecto

DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Mapeo de archivos de datos procesados
CLEAN_MATCHES_CSV = os.path.join(DATA_DIR, "clean_matches.csv")
FIFA_RANKINGS_CSV = os.path.join(DATA_DIR, "teams_elo_ranking.csv")  # Ranking FIFA y Elo consolidado
JUGADORES_VALORES_CSV = os.path.join(DATA_DIR, "jugadores_valores.csv")
WORLD_CUP_GROUPS_CSV = os.path.join(DATA_DIR, "world_cup_groups.csv")

# Parámetros para las simulaciones y el modelo
HISTORIC_MATCH_LIMIT = 15   # Límite de partidos para promedios de goles
NUM_SIMULATIONS = 100000   # Iteraciones de simulación Monte Carlo para versus