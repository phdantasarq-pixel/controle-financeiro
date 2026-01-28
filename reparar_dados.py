import pandas as pd
import json
import os

# Ajustado para procurar na RAIZ do projeto
FILE_PATH = "dados.json"

if os.path.exists(FILE_PATH):
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    df = pd.DataFrame(dados)

    print(f"Lendo {len(df)} registros...")

    # Converte todas as datas para o formato curto YYYY-MM-DD
    # errors='coerce' transforma o que for bizarro em NaT (nulo)
    df['data_vencimento'] = pd.to_datetime(df['data_vencimento'], format='mixed', errors='coerce')

    # Se alguma data falhou, vamos colocar a data de hoje para não perder o registro
    df['data_vencimento'] = df['data_vencimento'].fillna(pd.Timestamp.now())

    # Converte de volta para string no formato que o PlanejAI ama
    df['data_vencimento'] = df['data_vencimento'].dt.strftime('%Y-%m-%d')

    # Salva o JSON limpo por cima do antigo
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(df.to_dict(orient='records'), f, indent=4, ensure_ascii=False)

    print("✅ Banco de dados PlanejAI reparado com sucesso na raiz!")
else:
    print(f"❌ Erro: O arquivo '{FILE_PATH}' não foi encontrado na raiz do projeto.")
    print("Verifique se o nome é exatamente 'dados.json' (tudo minúsculo).")