import os
import io
import time
import requests
import pandas as pd

def fetch_all_pages_rankings():
    """
    Recorre las páginas de football-ranking.com de forma iterativa 
    para extraer el ranking completo de todas las selecciones del mundo.
    """
    print("Iniciando extracción multi-página de Rankings FIFA...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    all_tables = []
    
    # Recorremos de la página 1 a la 5 para asegurarnos de capturar los más de 200 países
    for page in range(1, 6):
        url = f"https://football-ranking.com/fifa-rankings?page={page}"
        print(f"Descargando bloque {page}/5...")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Procesamos el HTML de esta página en memoria
            html_stream = io.StringIO(response.text)
            tables = pd.read_html(html_stream)
            
            if tables:
                df_page = tables[0]
                all_tables.append(df_page)
            
            # Retardo para evitar sobrecarga en el servidor destino
            time.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Error al descargar la página {page}: {e}")
            break
            
    if not all_tables:
        print("❌ No se pudo descargar ninguna tabla.")
        return False
        
    # Concatenar y unificar los datos obtenidos
    print("📊 Consolidando y limpiando base de datos global...")
    df_global = pd.concat(all_tables, ignore_index=True)
    
    try:
        # Extraemos las dos primeras columnas: Posición y Nombre del Equipo
        df_clean = df_global.iloc[:, [0, 1]].copy()
        df_clean.columns = ['fifa_rank', 'team']
        
        # Limpieza de nombres comunes para match perfecto con tu dataset de Kaggle
        df_clean['team'] = df_clean['team'].str.strip()
        df_clean['team'] = df_clean['team'].replace({
            'United States': 'USA',
            'South Korea': 'Korea Republic',
            'Cape Verde': 'Cabo Verde',
            'Ivory Coast': "Côte d'Ivoire",
            'Scotland': 'Scotland',
            'Haiti': 'Haiti'
        })
        
        # Aseguramos formato numérico para los puestos
        df_clean['fifa_rank'] = pd.to_numeric(df_clean['fifa_rank'], errors='coerce')
        df_clean = df_clean.dropna(subset=['fifa_rank', 'team'])
        df_clean['fifa_rank'] = df_clean['fifa_rank'].astype(int)
        
        # Guardamos el archivo final unificado
        os.makedirs("data", exist_ok=True)
        output_path = "data/fifa_rankings.csv"
        df_clean.to_csv(output_path, index=False)
        
        print(f"Pipeline completado. Archivo guardado en: {output_path}")
        print(f"📊 Total de selecciones mundiales indexadas con éxito: {len(df_clean)}")
        return True

    except Exception as e:
        print(f"❌ Error durante la estructuración de datos: {e}")
        return False

if __name__ == "__main__":
    fetch_all_pages_rankings()