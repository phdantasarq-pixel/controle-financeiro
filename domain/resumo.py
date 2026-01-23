# domain/resumo.py
import pandas as pd


def resumo_mensal(df, mes_selecionado):
    if df.empty:
        return 0.0, 0.0, 0.0

    # Criamos uma cópia para garantir que não alteramos o estado global
    df_copy = df.copy()

    # Garante que a coluna de vencimento seja datetime
    df_copy['data_vencimento'] = pd.to_datetime(df_copy['data_vencimento'])

    try:
        # Ajuste para o formato MM/YYYY
        # Se mes_selecionado for "01/2026", o split('/') gera ["01", "2026"]
        mes_filtro = int(mes_selecionado.split('/')[0])
        ano_filtro = int(mes_selecionado.split('/')[1])
    except (ValueError, IndexError):
        # Fallback caso o formato ainda venha como YYYY-MM em algum contexto
        try:
            ano_filtro = int(mes_selecionado.split('-')[0])
            mes_filtro = int(mes_selecionado.split('-')[1])
        except:
            return 0.0, 0.0, 0.0

    # Filtrar os dados pelo mês e ano de VENCIMENTO
    mask = (df_copy['data_vencimento'].dt.month == mes_filtro) & \
           (df_copy['data_vencimento'].dt.year == ano_filtro)

    df_mes = df_copy[mask]

    # Cálculos de Receitas e Despesas
    receitas = df_mes[df_mes['tipo'] == 'Receita']['valor'].sum()
    despesas = df_mes[df_mes['tipo'] == 'Despesa']['valor'].sum()
    saldo = receitas - despesas

    return float(receitas), float(despesas), float(saldo)