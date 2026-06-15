import os
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.tree import plot_tree

def generate_model_graphics():
    print("🧠 Cargando el cerebro de la IA y los datos...")
    model_path = os.path.join("models", "world_cup_predictor.joblib")
    matches_path = os.path.join("data", "matches_with_elo.csv")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError("❌ Primero debes entrenar el modelo con train_model.py")
        
    model = joblib.load(model_path)
    
    # Nombres de las variables en el mismo orden estricto
    feature_names = ['elo_difference', 'is_neutral', 'goals_scored_diff', 'goals_conceded_diff', 'form_difference']
    class_names = ['Gana Visitante', 'Empate', 'Gana Local']
    
    # --- GRÁFICO 1: IMPORTANCIA DE VARIABLES ---
    print("📊 Generando gráfico de Importancia de Variables...")
    importances = model.feature_importances_
    forest_importances = pd.Series(importances, index=feature_names).sort_values(ascending=True)
    
    plt.figure(figsize=(10, 5))
    # Usamos un diseño plano y limpio (flat/minimalist) con un color sólido
    colors = ['#bdc3c7', '#95a5a6', '#7f8c8d', '#34495e', '#2c3e50'] 
    forest_importances.plot(kind='barh', color='#2c3e50', edgecolor='none')
    
    plt.title("¿En qué se basa la IA para predecir? (Importancia de Variables)", fontsize=14, pad=15)
    plt.xlabel("Grado de Importancia (0.0 a 1.0)", fontsize=11)
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    
    # Quitar bordes innecesarios para diseño limpio
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
        
    os.makedirs("output", exist_ok=True)
    plt.tight_layout()
    plt.savefig(os.path.join("output", "importancia_variables.png"), dpi=300)
    plt.close()
    
    # --- GRÁFICO 2: VER UN ÁRBOL POR DENTRO ---
    print("🌳 Generando mapa visual de un Árbol de Decisión del Bosque...")
    plt.figure(figsize=(20, 10))
    
    # Tomamos el primer árbol del bosque (estimator[0]) y limitamos la vista a 3 niveles para que no sea un caos ilegible
    plot_tree(model.estimators_[0], 
              max_depth=3, 
              feature_names=feature_names, 
              class_names=class_names, 
              filled=True, 
              rounded=True, 
              fontsize=10)
              
    plt.title("Mapa de Decisiones de la IA (Estructura de un Árbol Interno)", fontsize=16, pad=20)
    plt.savefig(os.path.join("output", "arbol_decision.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n🎨 ¡Gráficos visuales generados con éxito!")
    print("📍 Revisa la nueva carpeta 'output/' dentro de tu proyecto. Ahí encontrarás:")
    print("   1. importancia_variables.png")
    print("   2. arbol_decision.png\n")

if __name__ == "__main__":
    try:
        generate_model_graphics()
    except Exception as e:
        print(f"❌ Ocurrió un error al graficar: {e}")