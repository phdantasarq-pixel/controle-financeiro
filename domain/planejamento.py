from services.calendar import mes_ano


def agrupar_por_mes(lancamentos):
    agrupado = {}

    for l in lancamentos:
        chave = mes_ano(l.data)
        agrupado.setdefault(chave, []).append(l)

    return agrupado
