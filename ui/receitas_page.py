import streamlit as st
from domain.receitas import Receita

def receitas_page(dados):
    st.header("💰 Valores a Receber")

    receitas = dados["receitas"]

    qtd = st.number_input("Quantidade de receitas", 1, 20, max(1, len(receitas)))

    for i in range(qtd):
        with st.expander(f"Receita {i+1}", expanded=True):
            col1, col2, col3, col4 = st.columns(4)

            pessoa = col1.text_input("Pessoa", key=f"r_p_{i}")
            pago = col2.number_input("Pago", step=10.0, key=f"r_pg_{i}")
            deve = col3.number_input("Deve", step=10.0, key=f"r_dv_{i}")
            desc = col4.text_input("Descrição", key=f"r_d_{i}")

            receitas.append(
                Receita(pessoa, pago, deve, desc).__dict__
            )
