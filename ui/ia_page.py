import streamlit as st
from services.ia_service import IAService
from datetime import datetime


def ia_page(df):
    st.header("🤖 Consultoria PlanejAI")
    st.caption("Inteligência Artificial analisando seus dados do MongoDB em tempo real.")

    with st.container(border=True):
        st.subheader("Análise Estratégica")
        st.write("Clique no botão abaixo para que o Gemini examine suas finanças.")

        mes_atual = datetime.now().strftime("%m/%Y")

        if st.button("✨ Gerar Insight Inteligente", use_container_width=True):
            with st.spinner("O PlanejAI está processando seus dados..."):
                ai = IAService()
                insight = ai.gerar_insight(df, mes_atual)

                st.markdown("---")
                st.markdown(insight)
                st.info("Nota: Esta análise é gerada por IA e deve servir como sugestão educacional.")