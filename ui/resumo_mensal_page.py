import streamlit as st
import pandas as pd
import plotly.express as px
import json
from ui.components import seletor_meses_inteligente
from services.database import Database
from ui.layout import page_header


def processar_dados_detalhados_resumo(df_despesas):
    registros = []
    for _, row in df_despesas.iterrows():
        detalhes = row.get('detalhes')
        sucesso_expansao = False

        try:
            itens = json.loads(detalhes) if isinstance(detalhes, str) else detalhes
            if isinstance(itens, list) and len(itens) > 0:
                for it in itens:
                    registros.append({
                        "valor": float(it.get('valor', 0)),
                        "categoria": it.get('categoria', 'Outro'),
                        "descricao": it.get('descricao', it.get('item', row['descricao']))
                    })
                sucesso_expansao = True
        except:
            pass

        # Só adicionamos o registro original se:
        # 1. Não foi expandido pela IA
        # 2. NÃO for da categoria "Cartão de Crédito" (para limpar o gráfico)
        if not sucesso_expansao and row['categoria'] != "Cartão de Crédito":
            registros.append({
                "valor": row['valor'],
                "categoria": row['categoria'],
                "descricao": row['descricao']
            })

    return pd.DataFrame(registros) if registros else pd.DataFrame(columns=["valor", "categoria", "descricao"])


def resumo_mensal_page(df):
    page_header("🏠 Resumo Mensal", "Cockpit de Gestão PlanejAI")

    if df.empty:
        st.warning("Sem dados para gerar o resumo.")
        return

    # --- 1. SELETOR E FILTRO ---
    mes_sel = seletor_meses_inteligente(key_suffix="resumo_geral")
    mes_f, ano_f = map(int, mes_sel.split('/'))

    df_proc = df.copy()
    df_proc['data_vencimento'] = pd.to_datetime(df_proc['data_vencimento'], errors='coerce')
    df_mes = df_proc[
        (df_proc['data_vencimento'].dt.month == mes_f) & (df_proc['data_vencimento'].dt.year == ano_f)].copy()

    # --- 2. CÁLCULOS (MANTIDOS INTEGRALMENTE) ---
    receitas_mes = df_mes[df_mes['tipo'] == "Receita"]['valor'].sum()
    df_despesas_mes = df_mes[df_mes['tipo'] == "Despesa"].copy()
    total_despesas_mes = df_despesas_mes['valor'].sum()

    custos_fixos = df_despesas_mes[df_despesas_mes['natureza'] == "Fixo"]['valor'].sum()
    custos_variaveis = df_despesas_mes[df_despesas_mes['natureza'] == "Variável"]['valor'].sum()

    resultado_mes = receitas_mes - total_despesas_mes
    saldo_atual_contas = Database.obter_total_saldos_real()
    sobra_liquida_final = saldo_atual_contas + resultado_mes

    # --- SEÇÃO 1: MÉTRICAS (MANTIDAS) ---
    with st.container(border=True):
        st.subheader(f"📊 Performance de {mes_sel}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo em Contas (Hoje) 🏦", f"R$ {saldo_atual_contas:,.2f}")
        c2.metric("Entradas (Mês)", f"R$ {receitas_mes:,.2f}")
        c3.metric("Total Despesas (Mês)", f"R$ {total_despesas_mes:,.2f}",
                  delta=f"-{total_despesas_mes:,.2f}", delta_color="inverse")
        st.divider()
        c4, c5, c6 = st.columns(3)
        c4.metric("Resultado Mensal", f"R$ {resultado_mes:,.2f}",
                  delta="Superavit" if resultado_mes >= 0 else "Deficit")
        cor_sobra = "normal" if sobra_liquida_final >= 0 else "inverse"
        c5.metric("Sobra Projetada (Fim do Mês)", f"R$ {sobra_liquida_final:,.2f}",
                  delta="Disponível", delta_color=cor_sobra)
        comprometimento = (total_despesas_mes / receitas_mes * 100) if receitas_mes > 0 else 0
        c6.metric("Comprometimento", f"{comprometimento:.1f}%",
                  delta="Cuidado!" if comprometimento > 70 else "Saudável",
                  delta_color="inverse" if comprometimento > 70 else "normal")
        st.divider()
        _, c7, c8, _ = st.columns([0.5, 1, 1, 0.5])
        c7.metric("Total Gastos Fixos 📌", f"R$ {custos_fixos:,.2f}")
        c8.metric("Total Gastos Variáveis 💸", f"R$ {custos_variaveis:,.2f}")

    # --- SEÇÃO 2: TENDÊNCIA E NATUREZA (MANTIDAS) ---
    col_t, col_n = st.columns([2, 1])
    with col_t:
        with st.container(border=True):
            st.markdown("**📅 Fluxo de Despesas**")
            if not df_despesas_mes.empty:
                df_daily = df_despesas_mes.groupby(df_despesas_mes['data_vencimento'].dt.day)[
                    'valor'].sum().reset_index()
                fig_l = px.line(df_daily, x='data_vencimento', y='valor', markers=True,
                                color_discrete_sequence=['#FF4B4B'])
                fig_l.update_layout(height=220, margin=dict(t=5, b=5, l=5, r=5))
                st.plotly_chart(fig_l, use_container_width=True)

    with col_n:
        with st.container(border=True):
            st.markdown("**⚖️ Proporção Fixos/Var.**")
            df_nat = pd.DataFrame({'Nat': ['Fixo', 'Var'], 'Total': [custos_fixos, custos_variaveis]})
            fig_b = px.bar(df_nat, x='Nat', y='Total', color='Nat',
                           color_discrete_map={'Fixo': '#1f77b4', 'Var': '#ff7f0e'})
            fig_b.update_layout(height=220, showlegend=False, margin=dict(t=5, b=5, l=5, r=5))
            st.plotly_chart(fig_b, use_container_width=True)

    # --- SEÇÃO 3: DETALHAMENTO (APLICADA A INTELIGÊNCIA DE IA) ---
    st.markdown("---")
    st.subheader("🔍 Detalhamento de Gastos")

    if not df_despesas_mes.empty:
        # Aplicamos o processamento detalhado apenas para os gráficos abaixo
        df_analise = processar_dados_detalhados_resumo(df_despesas_mes)

        col_pizza, col_top = st.columns([1.4, 1])

        with col_pizza:
            with st.container(border=True):
                st.markdown("**Gastos por Categoria**")
                df_p = df_analise.groupby('categoria')['valor'].sum().reset_index()
                fig_p = px.pie(df_p, values='valor', names='categoria', hole=0.5)
                fig_p.update_layout(
                    height=400,
                    margin=dict(t=30, b=30, l=10, r=10),
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
                )
                st.plotly_chart(fig_p, use_container_width=True)

        with col_top:
            with st.container(border=True, height=455):
                st.markdown("**🏆 Top 5 Desembolsos**")
                # Agora o Top 5 considera os itens individuais dentro da fatura!
                top5 = df_analise.sort_values(by='valor', ascending=False).head(5)
                for i, (_, row) in enumerate(top5.iterrows(), 1):
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #444; padding: 12px 0;">
                            <div>
                                <div style="font-weight: bold; font-size: 0.9rem;">{i}º {row['descricao'][:20]}</div>
                                <div style="font-size: 0.75rem; color: #888;">{row['categoria']}</div>
                            </div>
                            <div style="font-weight: bold; font-size: 1rem; color: #ff4b4b; text-align: right; min-width: 110px;">
                                R$ {row['valor']:,.2f}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    else:
        st.info("Nenhuma despesa registrada para este período.")