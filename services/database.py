import pandas as pd
import json
import os


class Database:
    # Caminho ajustado para a raiz
    FILE_PATH = "dados.json"

    @staticmethod
    def carregar_dados():
        if not os.path.exists(Database.FILE_PATH):
            return pd.DataFrame(columns=["data_vencimento", "tipo", "natureza", "valor", "categoria", "descricao"])

        try:
            with open(Database.FILE_PATH, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            df = pd.DataFrame(dados)
            if not df.empty:
                # Normaliza as datas no carregamento
                df['data_vencimento'] = pd.to_datetime(df['data_vencimento'], format='mixed', errors='coerce')
                df['data_vencimento'] = df['data_vencimento'].fillna(pd.Timestamp.now())
            return df
        except Exception:
            return pd.DataFrame(columns=["data_vencimento", "tipo", "natureza", "valor", "categoria", "descricao"])

    @staticmethod
    def salvar_dados(df):
        df_copy = df.copy()
        # Força conversão para datetime antes de formatar como string para o JSON
        df_copy['data_vencimento'] = pd.to_datetime(df_copy['data_vencimento'], format='mixed', errors='coerce')
        df_copy['data_vencimento'] = df_copy['data_vencimento'].dt.strftime('%Y-%m-%d')

        dados = df_copy.to_dict(orient='records')
        with open(Database.FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)