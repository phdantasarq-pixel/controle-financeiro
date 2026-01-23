import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
from services.calendar_service import mes_ano
from services.database import Database
from datetime import datetime


def resumo_page(df):
    # --- ESTILIZAÇÃO CSS (Apenas tamanho dos botões) ---
    st.markdown("""
        <style>
            /* Aumenta o tamanho e o destaque dos botões do Mês de Referência */
            div[data-testid="stSegmentedControl"] button {
                min-height: 55px; /* Botões mais altos */
                min-width: 80px;  /* Botões mais largos */
                font-weight: bold;
                font-size: 16px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.header("📊 Resumo Financeiro")

    # --- NAVEGAÇÃO: MÊS DE REFERÊNCIA ---
    opcoes = mes_ano()
    mes_atual_str = datetime.now().strftime("%m/%Y")

    try:
        indice_padrao = opcoes.index(mes_atual_str)
    except ValueError:
        indice_padrao = 0

    st.write("### 📅 Mês de Referência")

    mes_selecionado = st.segmented_control(
        label="Meses Disponíveis",
        options=opcoes,
        default=opcoes[indice_padrao],
        selection_mode="single",
        label_visibility="collapsed"
    )

    if not mes_selecionado:
        mes_selecionado = mes_atual_str

    # --- CÁLCULOS DAS MÉTRICAS (KPIs) ---
    receitas, despesas, saldo = resumo_mensal(df, mes_selecionado)

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo do Mês", f"R$ {saldo:,.2f}", delta=f"R$ {saldo:,.2f}")

    st.divider()

    # --- TABELA DE EXTRATO FILTRADA ---
    if not df.empty:
        # 1. PREPARAÇÃO E FILTRAGEM
        df_proc = df.copy()
        df_proc['data_vencimento'] = pd.to_datetime(df_proc['data_vencimento'])

        # Extrair mês e ano do botão selecionado
        mes_f = int(mes_selecionado.split('/')[0])
        ano_f = int(mes_selecionado.split('/')[1])

        # Filtra apenas o mês selecionado
        mask = (df_proc['data_vencimento'].dt.month == mes_f) & (df_proc['data_vencimento'].dt.year == ano_f)
        df_filtrado = df_proc[mask].sort_values(by="data_vencimento")

        st.subheader(f"Extrato Detalhado - {mes_selecionado}")

        if df_filtrado.empty:
            st.info(f"Nenhum lançamento encontrado para {mes_selecionado}.")
        else:
            # 2. LÓGICA DE PAGINAÇÃO (15 lançamentos)
            itens_por_pagina = 15
            total_registros = len(df_filtrado)
            total_paginas = max(1, (total_registros // itens_por_pagina) + (
                1 if total_registros % itens_por_pagina > 0 else 0))

            if total_paginas > 1:
                col_pag, _ = st.columns([2, 5])
                with col_pag:
                    pagina_atual = st.number_input(f"Página (Total: {total_paginas})",
                                                   min_value=1, max_value=total_paginas, value=1)

                inicio = (pagina_atual - 1) * itens_por_pagina
                fim = inicio + itens_por_pagina
                df_pagina = df_filtrado.iloc[inicio:fim]
            else:
                df_pagina = df_filtrado

            colunas_visiveis = ["data_vencimento", "tipo", "natureza", "valor", "categoria", "descricao"]

            # 3. EDITOR DE DADOS (Somente Edição)
            df_editado = st.data_editor(
                df_pagina,
                column_order=colunas_visiveis,
                use_container_width=True,
                num_rows="fixed",  # Bloqueia adição de novas linhas
                column_config={
                    "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                    "tipo": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"]),
                    "natureza": st.column_config.SelectboxColumn("Natureza", options=["Fixo", "Variável"]),
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                }
            )

            # 4. LÓGICA DE SALVAMENTO
            if not df_editado.equals(df_pagina):
                if st.button("💾 Salvar Alterações"):
                    # Atualiza o DF original nos índices corretos
                    df.loc[df_editado.index] = df_editado
                    st.session_state.df = df
                    if Database.salvar_dados(df):
                        st.success("Dados atualizados!")
                        st.rerun()
    else:
        st.info("O banco de dados está vazio.")