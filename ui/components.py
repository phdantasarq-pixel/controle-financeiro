import streamlit as st
import pandas as pd
from datetime import datetime


def seletor_meses_inteligente(key_suffix=""):
    """
    Componente de UI que exibe todos os meses do ano em foco.
    Botões laterais saltam para o ano anterior ou seguinte.
    """
    mes_foco_key = f"mes_foco_{key_suffix}"

    # Inicializa com o mês atual se não existir
    if mes_foco_key not in st.session_state:
        st.session_state[mes_foco_key] = datetime.now().strftime('%m/%Y')

    # Identifica o ano do mês que está em foco
    base_dt = datetime.strptime(st.session_state[mes_foco_key], "%m/%Y")
    ano_foco = base_dt.year

    # 1. Gera EXATAMENTE os 12 meses do ano em foco (Janeiro a Dezembro)
    meses_exibicao = [f"{m:02d}/{ano_foco}" for m in range(1, 13)]

    # Layout de colunas: [Seta -1Ano] [Meses] [Seta +1Ano]
    # Ajustei a proporção para os 12 botões caberem melhor
    c_retro, c_center, c_adv = st.columns([0.6, 8, 0.6])

    with c_retro:
        if st.button("⬅️", key=f"btn_prev_{key_suffix}", use_container_width=True, help="Ver ano anterior"):
            nova_data = base_dt - pd.DateOffset(years=1)
            st.session_state[mes_foco_key] = nova_data.strftime("%m/%Y")
            st.rerun()

    with c_center:
        # Exibe os 12 meses do ano atual
        mes_escolhido = st.segmented_control(
            f"Ano {ano_foco}",
            options=meses_exibicao,
            default=st.session_state[mes_foco_key],
            selection_mode="single",
            label_visibility="collapsed",  # Mantemos limpo, o ano já está implícito nos botões
            key=f"seg_control_{key_suffix}"
        )

        if mes_escolhido and mes_escolhido != st.session_state[mes_foco_key]:
            st.session_state[mes_foco_key] = mes_escolhido
            st.rerun()

    with c_adv:
        if st.button("➡️", key=f"btn_next_{key_suffix}", use_container_width=True, help="Ver próximo ano"):
            nova_data = base_dt + pd.DateOffset(years=1)
            st.session_state[mes_foco_key] = nova_data.strftime("%m/%Y")
            st.rerun()

    # Exibe em qual ano o usuário está navegando (opcional, para clareza)
    st.markdown(f"<p style='text-align: center; color: gray;'>Navegando em: <b>{ano_foco}</b></p>",
                unsafe_allow_html=True)

    return st.session_state[mes_foco_key]