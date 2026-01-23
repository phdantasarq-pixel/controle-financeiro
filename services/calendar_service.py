from datetime import datetime
import pandas as pd

def mes_ano():
    # Gera os últimos 12 meses para o usuário selecionar
    hoje = datetime.now()
    datas = pd.date_range(end=hoje, periods=12, freq='MS').sort_values(ascending=False)
    return [data.strftime('%m/%Y') for data in datas]