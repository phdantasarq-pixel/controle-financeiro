import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
from services.calendar_service import mes_ano
from datetime import datetime


def resumo_page(df):
    st.header("📊 Resumo Financeiro")

    opcoes = mes_ano()
    mes_sel = st.segmented_control("Meses", options=opcoes,
                                   default=datetime.now().strftime("%m/%Y")) or datetime.now().strftime("%m/%Y")

    receitas, despesas, saldo = resumo_mensal(df, mes_sel)
    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo", f"R$ {saldo:,.2f}")

    if not df.empty:
        df_p = df.copy()
        df_p['data_vencimento'] = pd.to_datetime(df_p['data_vencimento'], format='mixed')
        m, a = map(int, mes_sel.split('/'))
        df_f = df_p[(df_p['data_vencimento'].dt.month == m) & (df_p['data_vencimento'].dt.year == a)]

        st.dataframe(
            df_f.sort_values("data_vencimento"),
            use_container_width=True,
            hide_index=True,
            column_config={
                "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD-MM-YYYY"),
                "data_registro": st.column_config.DateColumn("Registro", format="DD-MM-YYYY"),
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "tipo": "Tipo", "natureza": "Natureza", "categoria": "Categoria", "descricao": "Descrição"
            }
        )