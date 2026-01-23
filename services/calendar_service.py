from datetime import datetime
from dateutil.relativedelta import relativedelta

def mes_ano():
    """
    Gera 13 períodos (MM/YYYY) em ordem cronológica.
    6 meses passados, o atual, e 6 meses futuros.
    """
    hoje = datetime.now()
    periodos = []

    # Gerar do mais antigo (-6) para o mais futuro (+6)
    for i in range(-6, 7):
        data = hoje + relativedelta(months=i)
        periodos.append(data.strftime("%m/%Y"))

    return periodos