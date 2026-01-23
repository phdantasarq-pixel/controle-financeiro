import json
import os

def caminho_mes(ano, mes):
    pasta = f"data/{ano}"
    os.makedirs(pasta, exist_ok=True)
    return f"{pasta}/{ano}-{mes:02d}.json"

def carregar_mes(ano, mes):
    try:
        with open(caminho_mes(ano, mes), "r") as f:
            return json.load(f)
    except:
        return {"despesas": [], "receitas": []}

def salvar_mes(ano, mes, dados):
    with open(caminho_mes(ano, mes), "w") as f:
        json.dump(dados, f, indent=2)
