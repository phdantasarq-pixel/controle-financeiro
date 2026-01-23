import json
from datetime import date
from domain.models import LancamentoFinanceiro

ARQUIVO = "dados.json"


def carregar_dados():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            bruto = json.load(f)
            return [
                LancamentoFinanceiro(
                    id=d["id"],
                    descricao=d["descricao"],
                    valor=d["valor"],
                    data=date.fromisoformat(d["data"]),
                    tipo=d["tipo"],
                    pago=d["pago"]
                )
                for d in bruto
            ]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def salvar_dados(lancamentos):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "id": l.id,
                    "descricao": l.descricao,
                    "valor": l.valor,
                    "data": l.data.isoformat(),
                    "tipo": l.tipo,
                    "pago": l.pago
                }
                for l in lancamentos
            ],
            f,
            indent=4,
            ensure_ascii=False
        )
