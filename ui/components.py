import streamlit as st
import pandas as pd
from datetime import datetime


def seletor_meses_inteligente(key_suffix=""):
    mes_foco_key = f"mes_foco_{key_suffix}"

    # Estado inicial
    if mes_foco_key not in st.session_state:
        st.session_state[mes_foco_key] = datetime.now().strftime("%m/%Y")

    base_dt = datetime.strptime(st.session_state[mes_foco_key], "%m/%Y")
    ano_foco = base_dt.year
    mes_foco = base_dt.month

    # ---------- CSS DO COMPONENTE ----------
    st.markdown("""
    <style>
    .mes-grid button {
        background-color: #1e293b;
        color: #e5e7eb;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 6px 0;
        font-size: 0.75rem;
        font-weight: 500;
        width: 100%;
    }

    .mes-grid button:hover {
        background-color: #334155;
        border-color: #475569;
    }

    .mes-grid .ativo button {
        background-color: #ef4444;
        border-color: #ef4444;
        color: #ffffff;
        font-weight: 700;
    }

    .ano-label {
        text-align: center;
        font-weight: 700;
        color: #e5e7eb;
        margin-bottom: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- CONTROLES DE ANO ----------
    col_prev, col_title, col_next = st.columns([1, 6, 1])

    with col_prev:
        if st.button("⬅️", key=f"ano_prev_{key_suffix}", use_container_width=True):
            st.session_state[mes_foco_key] = f"{mes_foco:02d}/{ano_foco - 1}"
            st.rerun()

    with col_title:
        st.markdown(f"<div class='ano-label'>Ano {ano_foco}</div>", unsafe_allow_html=True)

    with col_next:
        if st.button("➡️", key=f"ano_next_{key_suffix}", use_container_width=True):
            st.session_state[mes_foco_key] = f"{mes_foco:02d}/{ano_foco + 1}"
            st.rerun()

    # ---------- GRID DE MESES ----------
    meses = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]

    rows = [meses[i:i+6] for i in range(0, 12, 6)]

    for linha in rows:
        cols = st.columns(len(linha))
        for idx, nome in enumerate(linha):
            mes_num = meses.index(nome) + 1
            ativo = mes_num == mes_foco

            with cols[idx]:
                container_class = "ativo mes-grid" if ativo else "mes-grid"
                st.markdown(f"<div class='{container_class}'>", unsafe_allow_html=True)

                if st.button(
                    nome,
                    key=f"mes_{mes_num}_{key_suffix}",
                    use_container_width=True
                ):
                    st.session_state[mes_foco_key] = f"{mes_num:02d}/{ano_foco}"
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

    return st.session_state[mes_foco_key]
