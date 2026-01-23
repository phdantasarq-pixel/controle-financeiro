from datetime import date
from dateutil.relativedelta import relativedelta


def mes_para_str(d: date) -> str:
    """Converte date para YYYY-MM"""
    return d.strftime("%Y-%m")


def gerar_meses(
    meses_passados: int = 12,
    meses_futuros: int = 6
) -> list[str]:
    """
    Gera lista de meses no formato YYYY-MM
    Ex:
    ['2025-01', '2025-02', ..., '2026-06']
    """
    hoje = date.today().replace(day=1)
    inicio = hoje - relativedelta(months=meses_passados)

    meses = []
    total = meses_passados + meses_futuros + 1

    for i in range(total):
        mes = inicio + relativedelta(months=i)
        meses.append(mes_para_str(mes))

    return meses


def meses_disponiveis() -> list[str]:
    """
    Função usada pela UI (sidebar)
    """
    return gerar_meses(
        meses_passados=24,  # histórico ilimitado prático
        meses_futuros=6     # planejamento
    )
