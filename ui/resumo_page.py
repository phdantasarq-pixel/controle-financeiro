import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
from services.calendar_service import mes_ano
from services.database import Database
from datetime import datetime


def resumo_page(df):
    # --- ESTILIZAÇÃO CSS CORRIGIDA ---
    st.markdown("""
        <style>
            /* Altera a cor do botão selecionado para Verde */
            div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
                background-color: #28a745 !important;
                color: white !important;
                border-color: #28a745 !important;
            }
            /* Aumenta o tamanho e destaque dos botões */
            div[data-testid="stSegmentedControl"] button {
                min-height: 50px;
                font-weight: bold;
                font-size: 16px;
            }
        </style>
    """, unsafe_allow_html=True)  # Corrigido para unsafe_allow_html

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

    # --- CÁLCULOS E MÉTRICAS ---
    receitas, despesas, saldo = resumo_mensal(df, mes_selecionado)

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo do Mês", f"R$ {saldo:,.2f}", delta=f"R$ {saldo:,.2f}")

    st.divider()

    # --- TABELA DE EXTRATO COM PAGINAÇÃO ---
    if not df.empty:
        st.subheader("Extrato Detalhado")

        # 1. Preparação e Ordenação por Vencimento
        df_exibicao = df.copy()
        df_exibicao['data_vencimento'] = pd.to_datetime(df_exibicao['data_vencimento'])
        df_exibicao = df_exibicao.sort_values(by="data_vencimento")

        # 2. Lógica de Paginação (15 lançamentos por vez)
        itens_por_pagina = 15
        total_registros = len(df_exibicao)
        total_paginas = max(1, (total_registros // itens_por_pagina) + (
            1 if total_registros % itens_por_pagina > 0 else 0))

        # Só exibe seletor de página se houver mais de uma
        if total_paginas > 1:
            col_pag, _ = st.columns([2, 5])
            with col_pag:
                pagina_atual = st.number_input(f"Página (Total: {total_paginas})",
                                               min_value=1, max_value=total_paginas, value=1)

            inicio = (pagina_atual - 1) * itens_por_pagina
            fim = inicio + itens_por_pagina
            df_pagina = df_exibicao.iloc[inicio:fim]
        else:
            df_pagina = df_exibicao

        colunas_visiveis = ["data_vencimento", "tipo", "natureza", "valor", "categoria", "descricao"]

        # 3. Editor de Dados (Somente Edição, sem Adição de novas linhas)
        df_editado = st.data_editor(
            df_pagina,
            column_order=colunas_visiveis,
            use_container_width=True,
            num_rows="fixed",  # Impede adicionar/remover registros aqui
            column_config={
                "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"]),
                "natureza": st.column_config.SelectboxColumn("Natureza", options=["Fixo", "Variável"]),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "categoria": st.column_config.TextColumn("Categoria"),
                "descricao": st.column_config.TextColumn("Descrição")
            }
        )

        # 4. Lógica de Salvamento
        if not df_editado.equals(df_pagina):
            if st.button("💾 Salvar Alterações da Página"):
                # Atualiza as linhas editadas de volta no DataFrame original
                df.loc[df_editado.index] = df_editado
                st.session_state.df = df
                if Database.salvar_dados(df):
                    st.success("Dados atualizados com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhum lançamento encontrado para exibição.")