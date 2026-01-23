import streamlit as st
from domain.despesas import Despesa

def despesas_page(dados):
    st.header("📌 Despesas do mês")

    despesas = dados["despesas"]

    qtd = st.number_input("Quantidade de despesas", 1, 30, max(1, len(despesas)))

    for i in range(qtd):
        with st.expander(f"Despesa {i+1}", expanded=True):
            col1, col2, col3 = st.columns(3)

            descricao = col1.text_input("Descrição", key=f"d_desc_{i}")
            divida = col2.number_input("Dívida", step=10.0, key=f"d_div_{i}")
            pago = col3.number_input("Pago", step=10.0, key=f"d_pag_{i}")

            tipo = col1.selectbox("Tipo", ["fixo", "variavel"], key=f"d_tipo_{i}")
            venc = col2.text_input("Vencimento", key=f"d_venc_{i}")
            valor = col3.number_input("Valor mensal", step=10.0, key=f"d_val_{i}")

            despesas.append(
                Despesa(descricao, divida, pago, tipo, venc, valor).__dict__
            )
