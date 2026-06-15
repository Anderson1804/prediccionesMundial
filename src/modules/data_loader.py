import pandas as pd
import modules.config as config

class DataLoader:
    @staticmethod
    def get_clean_matches():
        if not pd.io.common.file_exists(config.MATCHES_CSV):
            raise FileNotFoundError(f"❌ No se encuentra el archivo en: {config.MATCHES_CSV}")
        df = pd.read_csv(config.MATCHES_CSV)
        df['match_date'] = pd.to_datetime(df['match_date'])
        return df

    @staticmethod
    def get_fifa_rankings():
        if not pd.io.common.file_exists(config.RANKINGS_CSV):
            return pd.DataFrame(columns=['team', 'fifa_rank'])
        return pd.read_csv(config.RANKINGS_CSV)