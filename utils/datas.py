# utils/datas.py
from datetime import date, datetime
import calendar

# =========================
# 📅 Data atual
# =========================
def mes_ano_atual():
    hoje = date.today()
    return hoje.month, hoje.year


# =========================
# 🧾 Formatação de mês
# =========================
def formatar_mes(mes, ano):
    return f"{ano}-{mes:02d}"


# =========================
# 📆 Nome do mês (para UI)
# =========================
def nome_mes(mes):
    return calendar.month_name[mes]


# =========================
# 🗓️ Datas de quinzena
# =========================
def quinzenas_do_mes(mes, ano):
    return [
        date(ano, mes, 1),
        date(ano, mes, 15)
    ]


# =========================
# 📌 Verificar se data pertence ao mês
# =========================
def dentro_do_mes(data_obj, mes, ano):
    return data_obj.month == mes and data_obj.year == ano


# =========================
# 🔄 Converter string para data
# =========================
def parse_data(texto):
    """
    Espera formato DD/MM/YYYY
    """
    return datetime.strptime(texto, "%d/%m/%Y").date()


# =========================
# 📂 Nome do arquivo JSON do mês
# =========================
def arquivo_mes(ano, mes):
    return f"data/{ano}/{formatar_mes(mes, ano)}.json"


# =========================
# 📅 Lista de meses do ano
# =========================
def meses_do_ano():
    return list(range(1, 13))
