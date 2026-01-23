from services.calendar import mes_ano


def resumo_mensal(lancamentos, mes):
    receitas = sum(
        l.valor for l in lancamentos
        if l.tipo == "receita" and mes_ano(l.data) == mes
    )

    despesas = sum(
        l.valor for l in lancamentos
        if l.tipo == "despesa" and mes_ano(l.data) == mes
    )

    return receitas, despesas, receitas - despesas
