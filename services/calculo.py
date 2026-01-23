def total_despesas(despesas):
    fixos = sum(d.valor_mensal for d in despesas if d.tipo == "fixo")
    variaveis = sum(d.valor_mensal for d in despesas if d.tipo == "variavel")
    return fixos, variaveis, fixos + variaveis

def total_receitas(receitas):
    return sum(r.recebido for r in receitas)
