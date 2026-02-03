import streamlit as st
import pandas as pd
from datetime import datetime

def seletor_meses_inteligente(key_suffix=""):
    mes_foco_key = f"mes_foco_{key_suffix}"
    if mes_foco_key not in st.session_state:
        st.session_state[mes_foco_key] = datetime.now().strftime("%m/%Y")

    base_dt = datetime.strptime(st.session_state[mes_foco_key], "%m/%Y")
    ano_foco = base_dt.year
    mes_foco = base_dt.month

    # CONTROLES DE ANO
    col_prev, col_title, col_next = st.columns([1, 6, 1])
    with col_prev:
        if st.button("⬅️", key=f"ano_prev_{key_suffix}"):
            st.session_state[mes_foco_key] = f"{mes_foco:02d}/{ano_foco - 1}"
            st.rerun()
    with col_title:
        # CORREÇÃO AQUI: Usando var(--text-color) para garantir contraste
        st.markdown(
            f"""<p style='text-align:center; font-weight:bold; margin-bottom:0; color: var(--text-color);'>
                Ano {ano_foco}
            </p>""",
            unsafe_allow_html=True
        )
    with col_next:
        if st.button("➡️", key=f"ano_next_{key_suffix}"):
            st.session_state[mes_foco_key] = f"{mes_foco:02d}/{ano_foco + 1}"
            st.rerun()

    # GRID DE MESES
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    for i in range(0, 12, 6):
        cols = st.columns(6)
        for idx, nome in enumerate(meses[i:i+6]):
            num = i + idx + 1
            ativo = (num == mes_foco)
            with cols[idx]:
                # O botão primário usa a cor do tema, o secundário agora será forçado no CSS
                if st.button(nome, key=f"btn_{num}_{key_suffix}", use_container_width=True,
                             type="primary" if ativo else "secondary"):
                    st.session_state[mes_foco_key] = f"{num:02d}/{ano_foco}"
                    st.rerun()

    return st.session_state[mes_foco_key]