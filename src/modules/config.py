import os

# --- CONTROL DE RUTAS DINÁMICAS ---
MODULES_DIR = os.path.dirname(os.path.abspath(__file__)) # src/modules
SRC_DIR = os.path.dirname(MODULES_DIR)                  # src
BASE_DIR = os.path.dirname(SRC_DIR)                     # raíz del proyecto

DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# 📊 MAPEO EXACTO DE TU CAPTURA DE PANTALLA (DATA RECONCILIADA)
CLEAN_MATCHES_CSV = os.path.join(DATA_DIR, "clean_matches.csv")
FIFA_RANKINGS_CSV = os.path.join(DATA_DIR, "fifa_rankings.csv")
JUGADORES_VALORES_CSV = os.path.join(DATA_DIR, "jugadores_valores.csv")
MARKET_VALUES_CSV = os.path.join(DATA_DIR, "market_values.csv")
MATCHES_WITH_ELO_CSV = os.path.join(DATA_DIR, "matches_with_elo.csv")
TEAMS_ELO_RANKING_CSV = os.path.join(DATA_DIR, "teams_elo_ranking.csv")
WORLD_CUP_GROUPS_CSV = os.path.join(DATA_DIR, "world_cup_groups.csv")

# 📐 CONSTANTES DEL MOTOR MATEMÁTICO ESTOCÁSTICO
SAMPLE_SIZE = 25
TIME_DECAY_ALPHA = 0.002
BASE_ELO = 1500.0
NUM_SIMULATIONS = 100000  # Tus 100k iteraciones master centralizadas
MAX_GOALS_MATRIX = 6