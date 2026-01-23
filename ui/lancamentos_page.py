import streamlit as st
from datetime import date
from domain.models import LancamentoFinanceiro
from services.storage import salvar_dados


def lancamentos_page(lancamentos):
    st.title("💰 Lançamentos")

    with st.form("novo"):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor", step=0.01)
        data_l = st.date_input("Data", value=date.today())
        tipo = st.selectbox("Tipo", ["receita", "despesa"])
        pago = st.checkbox("Pago?")
        salvar = st.form_submit_button("Salvar")

        if salvar:
            lancamentos.append(
                LancamentoFinanceiro.novo(
                    descricao, valor, data_l, tipo, pago
                )
            )
            salvar_dados(lancamentos)
            st.rerun()

    st.divider()

    for l in lancamentos:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.write(l.descricao)

        with col2:
            st.write(f"R$ {l.valor:.2f}")

        with col3:
            novo_pago = st.checkbox(
                "Pago",
                value=l.pago,
                key=f"pago-{l.id}"
            )
            l.pago = novo_pago

        with col4:
            if st.button("🗑️", key=f"del-{l.id}"):
                lancamentos.remove(l)
                salvar_dados(lancamentos)
                st.rerun()

    salvar_dados(lancamentos)
