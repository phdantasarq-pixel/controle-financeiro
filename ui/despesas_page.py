import streamlit as st
from datetime import date
from domain.despesa import Despesa
from domain.mappers import despesa_para_dict


def despesas_page(dados: dict):
    st.header("📉 Despesas")

    if "despesas" not in dados:
        dados["despesas"] = []

    with st.form("form_despesa"):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=50.0)
        tipo = st.selectbox("Tipo", ["fixo", "variavel"])
        vencimento = st.date_input("Vencimento", value=date.today())
        divida = st.checkbox("É dívida?")
        paga = st.checkbox("Já foi paga?")

        submitted = st.form_submit_button("➕ Adicionar despesa")

        if submitted:
            despesa = Despesa(
                descricao=descricao,
                divida=divida,
                paga=paga,
                tipo=tipo,
                vencimento=vencimento,
                valor=valor
            )

            dados["despesas"].append(despesa_para_dict(despesa))
            st.success("Despesa adicionada com sucesso!")
            st.rerun()

    st.divider()

    if not dados["despesas"]:
        st.info("Nenhuma despesa cadastrada.")
        return

    remover_index = None

    for i, d in enumerate(dados["despesas"]):
        with st.expander(f"{d['descricao']} — R$ {d['valor']:.2f}"):
            st.write(f"Tipo: {d['tipo']}")
            st.write(f"Vencimento: {d['vencimento']}")
            st.write(f"Dívida: {'Sim' if d['divida'] else 'Não'}")
            st.write(f"Status: {'Paga' if d['paga'] else 'Em aberto'}")

            if st.button("🗑️ Remover", key=f"remover_despesa_{i}"):
                remover_index = i

    if remover_index is not None:
        dados["despesas"].pop(remover_index)
        st.rerun()
