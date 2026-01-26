import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
from services.calendar_service import mes_ano
from services.database import Database
from datetime import datetime


def resumo_page(df):
    st.header("📊 Resumo Financeiro")
    opcoes = mes_ano()
    mes_atual = datetime.now().strftime("%m/%Y")
    mes_sel = st.segmented_control("Meses", options=opcoes, default=mes_atual, selection_mode="single") or mes_atual

    receitas, despesas, saldo = resumo_mensal(df, mes_sel)
    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo", f"R$ {saldo:,.2f}")

    if not df.empty:
        df_proc = df.copy()
        df_proc['data_vencimento'] = pd.to_datetime(df_proc['data_vencimento'], format='mixed')
        m, a = map(int, mes_sel.split('/'))
        df_f = df_proc[(df_proc['data_vencimento'].dt.month == m) & (df_proc['data_vencimento'].dt.year == a)]

        st.dataframe(df_f.sort_values("data_vencimento"), use_container_width=True)