import json
import os
import pandas as pd

# Sobe um nível para salvar o dados.json na raiz do projeto, fora da pasta services
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'dados.json')


class Database:
    @staticmethod
    def carregar_dados():
        """Lê o JSON e retorna um DataFrame do Pandas."""
        if not os.path.exists(DB_PATH):
            return pd.DataFrame(columns=['data', 'tipo', 'valor', 'categoria', 'descricao'])

        try:
            df = pd.read_json(DB_PATH, orient='records')
            if not df.empty:
                df['data'] = pd.to_datetime(df['data'])
            return df
        except Exception:
            return pd.DataFrame(columns=['data', 'tipo', 'valor', 'categoria', 'descricao'])

    @staticmethod
    def salvar_dados(df):
        """Salva o DataFrame no arquivo JSON na raiz do projeto."""
        try:
            df.to_json(DB_PATH, orient='records', date_format='iso', indent=4, force_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return False