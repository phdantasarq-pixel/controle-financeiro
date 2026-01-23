import streamlit as st
from datetime import date
from domain.receita import Receita
from domain.mappers import receita_para_dict


def receitas_page(dados: dict):
    st.header("💰 A Receber")

    if "receitas" not in dados:
        dados["receitas"] = []

    with st.form("form_receita"):
        descricao = st.text_input("Origem / Pessoa")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=50.0)
        data_recebimento = st.date_input("Data", value=date.today())
        recebido = st.checkbox("Já recebido?")

        submitted = st.form_submit_button("➕ Adicionar receita")

        if submitted:
            receita = Receita(
                descricao=descricao,
                valor=valor,
                recebido=recebido,
                data=data_recebimento
            )

            dados["receitas"].append(receita_para_dict(receita))
            st.success("Receita adicionada com sucesso!")
            st.rerun()

    st.divider()

    if not dados["receitas"]:
        st.info("Nenhuma receita cadastrada.")
        return

    remover_index = None

    for i, r in enumerate(dados["receitas"]):
        with st.expander(f"{r['descricao']} — R$ {r['valor']:.2f}"):
            st.write(f"Data: {r['data']}")
            st.write(f"Status: {'Recebido' if r['recebido'] else 'Pendente'}")

            if st.button("🗑️ Remover", key=f"remover_receita_{i}"):
                remover_index = i

    if remover_index is not None:
        dados["receitas"].pop(remover_index)
        st.rerun()
