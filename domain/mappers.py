from datetime import datetime
from domain.despesa import Despesa
from domain.receita import Receita


FORMATO_DATA = "%Y-%m-%d"


def despesa_para_dict(d: Despesa) -> dict:
    return {
        "descricao": d.descricao,
        "divida": d.divida,
        "paga": d.paga,
        "tipo": d.tipo,
        "vencimento": d.vencimento.strftime(FORMATO_DATA),
        "valor": d.valor
    }


def dict_para_despesa(d: dict) -> Despesa:
    return Despesa(
        descricao=d["descricao"],
        divida=d["divida"],
        paga=d["paga"],
        tipo=d["tipo"],
        vencimento=datetime.strptime(
            d["vencimento"], FORMATO_DATA
        ).date(),
        valor=d["valor"]
    )


def receita_para_dict(r: Receita) -> dict:
    return {
        "descricao": r.descricao,
        "valor": r.valor,
        "recebido": r.recebido,
        "data": r.data.strftime(FORMATO_DATA)
    }


def dict_para_receita(r: dict) -> Receita:
    return Receita(
        descricao=r["descricao"],
        valor=r["valor"],
        recebido=r["recebido"],
        data=datetime.strptime(
            r["data"], FORMATO_DATA
        ).date()
    )
