import streamlit as st
from datetime import date
from domain.models import LancamentoFinanceiro
from services.storage import salvar_dados


def lancamentos_page(lancamentos):
    st.title("💰 Lançamentos")

    # --- FORMULÁRIO DE NOVO LANÇAMENTO ---
    with st.form("novo_lancamento", clear_on_submit=True):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor", step=0.01, min_value=0.0)
        data_l = st.date_input("Data", value=date.today())
        tipo = st.selectbox("Tipo", ["receita", "despesa"])
        pago = st.checkbox("Pago?")
        salvar = st.form_submit_button("Salvar")

        if salvar:
            if not descricao or valor <= 0:
                st.warning("Informe uma descrição e um valor válido.")
            else:
                lancamentos.append(
                    LancamentoFinanceiro.novo(
                        descricao=descricao,
                        valor=valor,
                        data=data_l,
                        tipo=tipo,
                        pago=pago,
                    )
                )
                salvar_dados(lancamentos)
                st.rerun()

    st.divider()

    # --- LISTAGEM DE LANÇAMENTOS ---
    for l in list(lancamentos):  # cópia para evitar erro ao remover
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.write(l.descricao)

        with col2:
            st.write(f"R$ {l.valor:.2f}")

        with col3:
            novo_pago = st.checkbox(
                "Pago",
                value=l.pago,
                key=f"pago-{l.id}",
            )

            if novo_pago != l.pago:
                l.pago = novo_pago
                salvar_dados(lancamentos)

        with col4:
            if st.button("🗑️", key=f"del-{l.id}"):
                lancamentos.remove(l)
                salvar_dados(lancamentos)
                st.rerun()

    # --- GARANTIA DE PERSISTÊNCIA FINAL ---
    salvar_dados(lancamentos)
