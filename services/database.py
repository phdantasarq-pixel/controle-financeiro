import json
import os
import pandas as pd

# Define o caminho para a raiz do projeto (sobe um nível a partir de services/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'dados.json')


class Database:
    @staticmethod
    def carregar_dados():
        """Lê o JSON, trata nomes de colunas antigos e garante tipos de dados corretos."""
        # Se o arquivo não existir, retorna um DataFrame vazio com a nova estrutura
        if not os.path.exists(DB_PATH):
            return pd.DataFrame(columns=[
                'data_registro', 'data_vencimento', 'tipo',
                'natureza', 'valor', 'categoria', 'descricao'
            ])

        try:
            df = pd.read_json(DB_PATH, orient='records')

            if not df.empty:
                # --- LÓGICA DE MIGRAÇÃO (Retrocompatibilidade) ---
                # Se encontrar a coluna 'data' antiga, renomeia para 'data_vencimento'
                if 'data' in df.columns:
                    df = df.rename(columns={'data': 'data_vencimento'})

                # Se a coluna 'natureza' não existir nos dados antigos, preenche como 'Variável'
                if 'natureza' not in df.columns:
                    df['natureza'] = 'Variável'

                # Se 'data_registro' não existir, usa a própria 'data_vencimento' como registro inicial
                if 'data_registro' not in df.columns:
                    df['data_registro'] = df['data_vencimento']

                # --- TRATAMENTO DE TIPOS ---
                # Garante que as colunas de data sejam objetos datetime do Pandas
                df['data_registro'] = pd.to_datetime(df['data_registro'])
                df['data_vencimento'] = pd.to_datetime(df['data_vencimento'])

            return df

        except Exception as e:
            print(f"Erro ao carregar banco de dados: {e}")
            # Em caso de erro crítico no JSON, retorna estrutura vazia para não travar o App
            return pd.DataFrame(columns=[
                'data_registro', 'data_vencimento', 'tipo',
                'natureza', 'valor', 'categoria', 'descricao'
            ])

    @staticmethod
    def salvar_dados(df):
        """Salva o DataFrame no arquivo JSON na raiz do projeto."""
        try:
            # Salva com indentação para ser legível e suporte a caracteres especiais (UTF-8)
            df.to_json(
                DB_PATH,
                orient='records',
                date_format='iso',
                indent=4,
                force_ascii=False
            )
            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return False