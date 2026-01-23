from domain.despesa import Despesa
from domain.receita import Receita


def resumo_mensal(despesas: list[Despesa], receitas: list[Receita]) -> dict:
    total_fixos = sum(
        d.valor for d in despesas if d.tipo == "fixo"
    )

    total_variaveis = sum(
        d.valor for d in despesas if d.tipo == "variavel"
    )

    total_despesas = total_fixos + total_variaveis

    total_receitas = sum(
        r.valor for r in receitas if r.recebido
    )

    saldo = total_receitas - total_despesas

    return {
        "fixos": total_fixos,
        "variaveis": total_variaveis,
        "despesas": total_despesas,
        "receitas": total_receitas,
        "saldo": saldo
    }
