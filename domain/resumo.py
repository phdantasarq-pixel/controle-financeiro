import pandas as pd


def resumo_mensal(df, mes_referencia):
    if df.empty:
        return 0.0, 0.0, 0.0

    df_copy = df.copy()
    # Garante que a coluna data seja datetime
    df_copy['data'] = pd.to_datetime(df_copy['data'])
    df_copy['mes_ano'] = df_copy['data'].dt.strftime('%m/%Y')

    df_filtrado = df_copy[df_copy['mes_ano'] == mes_referencia]

    receitas = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum()
    despesas = df_filtrado[df_filtrado['tipo'] == 'Despesa']['valor'].sum()
    saldo = receitas - despesas

    return receitas, despesas, saldo