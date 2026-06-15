import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier
import joblib

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def download_elo_data():
    print("📥 Descargando histórico desde Supabase...")
    local_path = os.path.join("data", "matches_with_elo.csv")
    with open(local_path, "wb") as f:
        res = supabase.storage.from_("datasets").download("matches_with_elo.csv")
        f.write(res)
    return pd.read_csv(local_path)

def prepare_features(df):
    print("⚙️ Construyendo el set de variables con pesos de torneo...")
    
    def determine_result(row):
        if row['home_score'] > row['away_score']: return 2
        elif row['home_score'] < row['away_score']: return 0
        else: return 1

    df['result'] = df.apply(determine_result, axis=1)
    
    # Variables definitivas
    df['elo_difference'] = df['home_elo_before'] - df['away_elo_before']
    df['is_neutral'] = df['neutral_bool'].astype(int)
    df['goals_scored_diff'] = df['home_goals_scored_avg'] - df['away_goals_avg'] if 'away_goals_avg' in df.columns else df['home_goals_scored_avg'] - df['away_goals_scored_avg']
    df['goals_conceded_diff'] = df['home_goals_conceded_avg'] - df['away_goals_conceded_avg']
    df['form_difference'] = df['home_form_avg'] - df['away_form_avg']
    
    # Nueva feature agregada al set
    features = ['elo_difference', 'is_neutral', 'goals_scored_diff', 'goals_conceded_diff', 'form_difference', 'tournament_weight']
    
    X = df[features]
    y = df['result']
    
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

def train_and_evaluate(X_train, X_test, y_train, y_test):
    print("🚀 Entrenando el modelo de Gradiente Descendente (XGBoost Classifier)...")
    
    # Configuramos los hiperparámetros óptimos para evitar sobreajuste
    model = XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='mlogloss'
    )
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n🎯 ¡ENTRENAMIENTO CONFIGURADO CON XGBOOST!")
    print(f"📊 Nueva Precisión del Modelo (Accuracy): {accuracy * 100:.2f}%\n")
    
    print("📝 Reporte de Clasificación Avanzado:")
    print(classification_report(y_test, y_pred, target_names=['Gana Visitante (0)', 'Empate (1)', 'Gana Local (2)']))
    
    return model

def save_and_upload_model(model):
    os.makedirs("models", exist_ok=True)
    model_path = os.path.join("models", "world_cup_predictor.joblib")
    joblib.dump(model, model_path)
    
    print("📤 Subiendo el cerebro XGBoost a Supabase Storage...")
    with open(model_path, 'rb') as f:
        supabase.storage.from_("datasets").upload(file=f, path="world_cup_predictor.joblib", file_options={"upsert": "true"})
    print("✅ ¡Pipeline de alta gama completado!")

if __name__ == "__main__":
    try:
        df_elo = download_elo_data()
        X_train, X_test, y_train, y_test = prepare_features(df_elo)
        trained_model = train_and_evaluate(X_train, X_test, y_train, y_test)
        save_and_upload_model(trained_model)
        print("\n=======================================================")
        input("🏁 Presiona ENTER para finalizar...")
    except Exception as e:
        print(f"❌ Error: {e}")
        input()