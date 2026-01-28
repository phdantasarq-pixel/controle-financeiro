import pandas as pd
import json
import os


class Database:
    FILE_PATH = "dados.json"

    @staticmethod
    def carregar_dados():
        if not os.path.exists(Database.FILE_PATH):
            return pd.DataFrame(
                columns=["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao"])

        try:
            with open(Database.FILE_PATH, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            df = pd.DataFrame(dados)
            if not df.empty:
                # Normaliza ambas as colunas de data
                for col in ['data_vencimento', 'data_registro']:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], format='mixed', errors='coerce')

                # Preenche valores nulos caso existam
                df['data_vencimento'] = df['data_vencimento'].fillna(pd.Timestamp.now())
                if 'data_registro' not in df.columns:
                    df['data_registro'] = pd.Timestamp.now()
                else:
                    df['data_registro'] = df['data_registro'].fillna(pd.Timestamp.now())

            return df
        except Exception:
            return pd.DataFrame(
                columns=["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao"])

    @staticmethod
    def salvar_dados(df):
        df_copy = df.copy()

        # Garante que as colunas sejam datetime antes de formatar
        df_copy['data_vencimento'] = pd.to_datetime(df_copy['data_vencimento'], errors='coerce')
        df_copy['data_registro'] = pd.to_datetime(df_copy['data_registro'], errors='coerce')

        # Arredonda para 2 casas decimais
        df_copy['valor'] = df_copy['valor'].astype(float).round(2)

        # Formata para string YYYY-MM-DD para o JSON
        df_copy['data_vencimento'] = df_copy['data_vencimento'].dt.strftime('%Y-%m-%d')
        df_copy['data_registro'] = df_copy['data_registro'].dt.strftime('%Y-%m-%d')

        dados = df_copy.to_dict(orient='records')
        with open(Database.FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)