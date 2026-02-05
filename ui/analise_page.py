import streamlit as st
import pandas as pd
import json
from domain.analise import (
    calcular_pareto_categorias,
    gerar_grafico_pareto,
    calcular_performance_pagamentos,
    gerar_grafico_performance
)


def processar_dados_detalhados(df_original):
    if df_original.empty:
        return df_original

    df_analise = df_original.copy()
    registros_expandidos = []
    indices_para_remover = []

    for idx, row in df_analise.iterrows():
        # Lógica inteligente: Se a categoria for Cartão de Crédito,
        # tentamos expandir. Se expandir com sucesso, removemos o 'Pai'.
        tem_detalhes = pd.notnull(row.get('detalhes')) and row['detalhes'] != ""

        if tem_detalhes:
            try:
                itens = json.loads(row['detalhes']) if isinstance(row['detalhes'], str) else row['detalhes']
                if itens:
                    indices_para_remover.append(idx)
                    for item in itens:
                        registros_expandidos.append({
                            "data_vencimento": row['data_vencimento'],
                            "tipo": "Despesa",
                            "categoria": item.get('categoria', 'Outro'),
                            "valor": float(item.get('valor', 0)),
                            "descricao": item.get('descricao', 'Item Fatura'),
                            "status": row.get('status', '🟡 Pendente')
                        })
            except:
                continue

        # REMOÇÃO ESTRATÉGICA: Se ainda for "Cartão de Crédito" e não conseguimos expandir,
        # removemos do gráfico para não poluir a análise de finalidade de gasto.
        elif row['categoria'] == "Cartão de Crédito":
            indices_para_remover.append(idx)

    df_analise = df_analise.drop(indices_para_remover)
    if registros_expandidos:
        df_analise = pd.concat([df_analise, pd.DataFrame(registros_expandidos)], ignore_index=True)

    return df_analise


def analise_categorias_page(df):
    st.header("🎯 Inteligência Financeira")
    st.write("Análise de eficiência, impacto de gastos e saúde circulatória.")

    if df.empty:
        st.warning("Sem dados suficientes para análise.")
        return

    # --- PROCESSAMENTO PARA GRÁFICOS (NOVO) ---
    # Criamos uma versão expandida para a análise de categorias não ser "cega" ao cartão
    df_expandido = processar_dados_detalhados(df)

    # --- LÓGICA DE CAPACIDADE DE RESERVA (BASEADA NO REAL) ---
    receita_total = df[df['tipo'] == "Receita"]['valor'].sum()
    despesa_total = df[df['tipo'] == "Despesa"]['valor'].sum()
    sobra_liquida = receita_total - despesa_total
    capacidade_aporte = (sobra_liquida / receita_total) * 100 if receita_total > 0 else 0

    # --- SEÇÃO 1: POTENCIAL DE RESERVA ---
    with st.container(border=True):
        st.subheader("🛡️ Potencial de Reserva (Mensal)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sobra Líquida", f"R$ {sobra_liquida:,.2f}")
        c2.metric("Capacidade de Aporte", f"{capacidade_aporte:.1f}%")
        c3.metric("Eficiência de Gastos", f"{(despesa_total / receita_total * 100) if receita_total > 0 else 0:.1f}%",
                  delta_color="inverse")
        st.progress(max(0.0, min(capacidade_aporte / 100, 1.0)))

    st.divider()

    # --- SEÇÃO 2: STATUS DE PAGAMENTOS (MANTIDO) ---
    # --- SEÇÃO 2: STATUS DE PAGAMENTOS (CORRIGIDO) ---
    st.subheader("🕒 Saúde do Fluxo de Caixa")
    df_status = calcular_performance_pagamentos(df)

    if df_status is not None and not df_status.empty:
        # Ajuste para reconhecer seus emojis de status
        pago = df_status[df_status['status'].str.contains('Concluído|Pago', case=False, na=False)]['valor'].sum()
        atrasado = df_status[df_status['status'].str.contains('Atrasado|Vencido', case=False, na=False)]['valor'].sum()

        # Pendente é tudo que não é pago nem atrasado
        total_geral = df_status['valor'].sum()
        pendente = total_geral - pago - atrasado

        total_despesas = pago + pendente + atrasado

        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"**Liquidado**\nR$ {pago:,.2f}")
            st.caption(f"{(pago / total_despesas * 100) if total_despesas > 0 else 0:.1f}% concluído")
        with col2:
            st.warning(f"**A Pagar**\nR$ {pendente:,.2f}")
            st.caption("Aguardando vencimento")
        with col3:
            st.error(f"**Em Atraso**\nR$ {atrasado:,.2f}")
            st.caption("Risco de juros e multas")

        st.write("**Progresso de Quitação Mensal:**")
        w_pago, w_pend, w_atra = max(pago, 0.01), max(pendente, 0.01), max(atrasado, 0.01)
        # Substitua os cols_barra por isso para uma visão única:
        st.write("**Distribuição do Fluxo:**")
        if total_despesas > 0:
            pct_pago = (pago / total_despesas) * 100
            pct_pend = (pendente / total_despesas) * 100
            pct_atra = (atrasado / total_despesas) * 100

            st.markdown(f"""
                <div style="display: flex; width: 100%; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="width: {pct_pago}%; background-color: #28a745;" title="Pago"></div>
                    <div style="width: {pct_pend}%; background-color: #ffc107;" title="Pendente"></div>
                    <div style="width: {pct_atra}%; background-color: #dc3545;" title="Atrasado"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 5px;">
                    <span>Concluído: {pct_pago:.1f}%</span>
                    <span>Pendente: {pct_pend:.1f}%</span>
                    <span>Atrasado: {pct_atra:.1f}%</span>
                </div>
            """, unsafe_allow_html=True)

    # --- SEÇÃO 3: ANÁLISE DE PARETO (USANDO DADOS EXPANDIDOS) ---
    st.subheader("📊 Onde está o seu dinheiro? (Pareto)")
    # IMPORTANTE: Aqui usamos o df_expandido para capturar os sub-itens da fatura
    df_pareto = calcular_pareto_categorias(df_expandido)

    if df_pareto is not None and not df_pareto.empty:
        viloes = df_pareto[df_pareto['acumulado'] <= 85]['categoria'].tolist()
        c_graf, c_viloes = st.columns([2, 1])

        with c_graf:
            fig_pareto = gerar_grafico_pareto(df_pareto)
            st.plotly_chart(fig_pareto, use_container_width=True)

        with c_viloes:
            st.markdown("### 🕵️ Os Vilões")
            if "Cartão de Crédito" in viloes: viloes.remove("Cartão de Crédito")  # Já está detalhado
            for i, cat in enumerate(viloes):
                st.error(f"{i + 1}º - {cat}")
            st.info("💡 Análise detalhada considerando itens de faturas importadas.")