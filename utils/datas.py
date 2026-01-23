# utils/datas.py
from datetime import date, datetime
import calendar
import locale

# Tenta configurar o calendário para português para exibir "Janeiro", "Fevereiro", etc.
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf-8')
except:
    # Fallback caso o sistema não tenha o locale instalado
    pass

# =========================
# 📅 Data atual
# =========================
def mes_ano_atual():
    hoje = date.today()
    return hoje.month, hoje.year


# =========================
# 🧾 Formatação de mês (Padrão para nome de pasta/arquivo)
# =========================
def formatar_mes(mes, ano):
    return f"{ano}-{mes:02d}"


# =========================
# 📆 Nome do mês (para UI em Português)
# =========================
def nome_mes(mes):
    # calendar.month_name[1] -> 'Janeiro'
    return calendar.month_name[mes].capitalize()


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
    # Garante que data_obj seja um objeto date ou datetime
    if isinstance(data_obj, str):
        data_obj = parse_data(data_obj)
    return data_obj.month == mes and data_obj.year == ano


# =========================
# 🔄 Converter string para data
# =========================
def parse_data(texto):
    """
    Converte string DD/MM/YYYY para objeto date
    """
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        # Tenta converter caso o pandas envie formato ISO (YYYY-MM-DD)
        return pd.to_datetime(texto).date()


# =========================
# 📂 Nome do arquivo JSON do mês
# =========================
def arquivo_mes(ano, mes):
    # Agora aponta para a raiz/data/ para ser consistente com sua branch
    return f"data/{ano}/{formatar_mes(mes, ano)}.json"


# =========================
# 📅 Lista de meses do ano
# =========================
def meses_do_ano():
    return list(range(1, 13))

# =========================
# 🇧🇷 Formatar objeto para String BR
# =========================
def formatar_data_br(data_obj):
    """
    Converte objeto date para string 'DD/MM/YYYY'
    """
    return data_obj.strftime("%d/%m/%Y")