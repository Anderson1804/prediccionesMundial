import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import modules.config as config

class Visualizer:
    @staticmethod
    def generate_heatmap(matrix_data, team_home, team_away):
        plt.figure(figsize=(8, 6.5))
        labels = [str(x) for x in range(config.MAX_GOALS_MATRIX)]
        
# Cambiamos los parámetros del heatmap para un acabado premium de diseño plano
        ax = sns.heatmap(
            matrix_data, 
            annot=True, 
            fmt=".1f", 
            cmap="Blues", 
            xticklabels=labels, 
            yticklabels=labels, 
            cbar=False,
            linewidths=1.5,        # ⬅️ Añade bordes finos y limpios entre casillas
            linecolor="#f8f9fa",   # ⬅️ Color de los bordes (blanco suave)
            annot_kws={"size": 9, "weight": "bold", "fontname": "sans-serif"} # ⬅️ Tipografía premium
        )
        ax.invert_yaxis()
        
        for text in ax.texts:
            text.set_text(text.get_text() + "%")
            
        plt.title(f"Matriz de Probabilidad Calibrada\n{team_home} vs {team_away}", fontsize=12, pad=15)
        plt.xlabel(f"Goles de {team_away}", fontsize=10, labelpad=10)
        plt.ylabel(f"Goles de {team_home}", fontsize=10, labelpad=10)
        
        for spine in ax.spines.values():
            spine.set_visible(False)
            
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        filename = f"matriz_probabilidad_{team_home}_vs_{team_away}.png"
        output_path = os.path.join(config.OUTPUT_DIR, filename)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        print(f"🎨 ¡Mapa de calor exportado con éxito en: {output_path}!\n")