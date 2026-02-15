import streamlit as st
import pandas as pd
from datetime import datetime

def seletor_meses_inteligente(key_suffix=""):
    mes_foco_key = f"mes_foco_{key_suffix}"
    if mes_foco_key not in st.session_state:
        st.session_state[mes_foco_key] = datetime.now().strftime("%m/%Y")

    base_dt = datetime.strptime(st.session_state[mes_foco_key], "%m/%Y")

    # Lista de nomes de meses
    meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    # --- UI COMPACTA (1 LINHA) ---
    col_ano_prev, col_ano, col_mes, col_ano_next = st.columns([0.5, 1.5, 4, 0.5])

    with col_ano_prev:
        if st.button("⬅️", key=f"prev_a_{key_suffix}", use_container_width=True):
            novo_ano = base_dt.year - 1
            st.session_state[mes_foco_key] = f"{base_dt.month:02d}/{novo_ano}"
            st.rerun()

    with col_ano:
        # Mostra o ano em destaque
        st.markdown(f"""
            <div style='text-align: center; background: rgba(255,255,255,0.05); 
            border-radius: 8px; padding: 5px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1);'>
                {base_dt.year}
            </div>
        """, unsafe_allow_html=True)

    with col_mes:
        # O pulo do gato: Um slider ou selectbox minimalista para o mês
        opcoes_meses = list(range(1, 13))
        mes_idx = st.select_slider(
            label="Mês",
            options=opcoes_meses,
            value=base_dt.month,
            format_func=lambda x: meses_nomes[x - 1],
            label_visibility="collapsed",
            key=f"slider_{key_suffix}"
        )
        if mes_idx != base_dt.month:
            st.session_state[mes_foco_key] = f"{mes_idx:02d}/{base_dt.year}"
            st.rerun()

    with col_ano_next:
        if st.button("➡️", key=f"next_a_{key_suffix}", use_container_width=True):
            novo_ano = base_dt.year + 1
            st.session_state[mes_foco_key] = f"{base_dt.month:02d}/{novo_ano}"
            st.rerun()

    return st.session_state[mes_foco_key]