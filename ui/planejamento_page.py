import streamlit as st
from domain.planejamento import agrupar_por_mes
from services.calendar_service import gerar_meses


def planejamento_page(lancamentos):
    st.title("📆 Planejamento Financeiro")

    meses = gerar_meses()
    agrupado = agrupar_por_mes(lancamentos)

    mes = st.selectbox("Selecione o mês", meses)

    total = 0.0
    for l in agrupado.get(mes, []):
        sinal = 1 if l.tipo == "receita" else -1
        total += l.valor * sinal

        st.write(
            f"{l.descricao} | {l.tipo} | R$ {l.valor:.2f}"
        )

    st.divider()
    st.metric("Saldo previsto", f"R$ {total:.2f}")
