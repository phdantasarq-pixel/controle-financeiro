import streamlit as st
from domain.resumo import resumo_mensal
from domain.mappers import dict_para_despesa, dict_para_receita


def resumo_page(dados: dict):
    st.header("📊 Resumo Mensal")

    despesas = [
        dict_para_despesa(d) for d in dados.get("despesas", [])
    ]
    receitas = [
        dict_para_receita(r) for r in dados.get("receitas", [])
    ]

    if not despesas and not receitas:
        st.info("Nenhum dado para gerar resumo.")
        return

    resumo = resumo_mensal(despesas, receitas)

    col1, col2, col3 = st.columns(3)

    col1.metric("Receitas", f"R$ {resumo['receitas']:.2f}")
    col2.metric("Despesas", f"R$ {resumo['despesas']:.2f}")
    col3.metric("Saldo", f"R$ {resumo['saldo']:.2f}")

    with st.expander("🔍 Detalhamento"):
        st.write(f"Fixos: R$ {resumo['fixos']:.2f}")
        st.write(f"Variáveis: R$ {resumo['variaveis']:.2f}")
