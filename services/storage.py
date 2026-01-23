import json
import os

ARQUIVO = "dados.json"


def estrutura_padrao():
    return {
        "despesas": [],
        "receitas": []
    }


def carregar_dados():
    if not os.path.exists(ARQUIVO):
        return estrutura_padrao()

    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Arquivo corrompido ou vazio
        return estrutura_padrao()


def salvar_dados(dados: dict):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
