def resumo_mensal(despesas, receitas):
    fixos = sum(d.valor_mensal for d in despesas if d.tipo == "fixo")
    variaveis = sum(d.valor_mensal for d in despesas if d.tipo == "variavel")
    total_despesas = fixos + variaveis
    total_receitas = sum(r.pago for r in receitas)

    return {
        "fixos": fixos,
        "variaveis": variaveis,
        "total_despesas": total_despesas,
        "total_receitas": total_receitas,
        "resultado": total_receitas - total_despesas
    }
