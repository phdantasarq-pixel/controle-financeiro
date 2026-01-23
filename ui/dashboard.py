import streamlit as st

def mostrar_metricas(df):
    col1, col2, col3 = st.columns(3)
    col1.metric("Saldo médio", f"R$ {df['saldo'].mean():,.2f}")
    col2.metric("Saldo final", f"R$ {df['saldo_acumulado'].iloc[-1]:,.2f}")
    col3.metric("Meses negativos", (df["saldo"] < 0).sum())

def mostrar_graficos(df):
    st.line_chart(df.set_index("mes")["saldo"])
    st.line_chart(df.set_index("mes")["saldo_acumulado"])
