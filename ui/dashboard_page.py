import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from ui.components import seletor_meses_inteligente
from services.database import Database
from ui.layout import page_header, section, card_container


def dashboard_page(df):
    st.markdown(
        "<style>div[data-testid='stSegmentedControl'] button {min-height: 55px; min-width: 80px; font-weight: bold;}</style>",
        unsafe_allow_html=True)
    st.header("📈 Dashboard Analítico")

    if df.empty:
        st.warning("Sem dados para gerar o Dashboard.")
        return

    # --- CÁLCULOS DE RESERVA (VERSÃO CORRIGIDA 2.0) ---
    df_reserva = df.copy()
    df_reserva['data_vencimento'] = pd.to_datetime(df_reserva['data_vencimento'], errors='coerce')

    # 1. Busca saldos que você JÁ TEM (Investimentos/Conta Corrente)
    df_saldos_manuais = Database.carregar_saldos()
    total_contas = df_saldos_manuais['valor'].sum() if not df_saldos_manuais.empty else 0

    # 2. Saldo Líquido do que entrou e saiu no sistema
    receitas_totais = df_reserva[df_reserva['tipo'] == "Receita"]['valor'].sum()
    despesas_totais = df_reserva[df_reserva['tipo'] == "Despesa"]['valor'].sum()
    saldo_extrato = receitas_totais - despesas_totais

    # 3. Reserva Real disponível hoje
    reserva_total_real = saldo_extrato + total_contas

    # 4. CÁLCULO DO CUSTO MÉDIO (Onde estava o erro)
    df_despesas = df_reserva[df_reserva['tipo'] == "Despesa"].copy()

    if not df_despesas.empty:
        # Criamos uma coluna de Mês/Ano para agrupar
        df_despesas['mes_ano'] = df_despesas['data_vencimento'].dt.to_period('M')

        # SOMA o total de gastos de CADA mês
        # Ex: Jan: 5000, Fev: 4500, Mar: 4800
        gastos_por_mes = df_despesas.groupby('mes_ano')['valor'].sum()

        # Tira a média desses totais mensais
        custo_medio = gastos_por_mes.mean()
        meta_reserva = custo_medio * 6
    else:
        custo_medio = 0
        meta_reserva = 0

    # --- UI DA RESERVA ---
    with st.container(border=True):
        st.subheader("🛡️ Saúde Financeira: Reserva de Emergência")
        c1, c2, c3 = st.columns([1, 1, 1.2])

        c1.metric("Custo Médio Mensal", f"R$ {custo_medio:,.2f}")
        c2.metric("Meta de Reserva (6 meses)", f"R$ {meta_reserva:,.2f}")

        if meta_reserva > 0:
            progresso = min(reserva_total_real / meta_reserva, 1.0) if reserva_total_real > 0 else 0
            c3.metric("Reserva Atual", f"R$ {reserva_total_real:,.2f}",
                      delta=f"{(progresso * 100):.1f}% da meta")

            st.progress(progresso)

            # Info Adicional
            meses_cobertos = reserva_total_real / custo_medio if custo_medio > 0 else 0
            st.write(f"💡 Seu saldo atual cobre **{meses_cobertos:.1f} meses** do seu custo de vida médio.")

    st.write("---")

    # --- TOP 5 MAIORES GASTOS DO MÊS SELECIONADO ---
    mes_sel = seletor_meses_inteligente(key_suffix="dash_analitico")
    mes_f, ano_f = map(int, mes_sel.split('/'))

    mask = (df_reserva['data_vencimento'].dt.month == mes_f) & (df_reserva['data_vencimento'].dt.year == ano_f)
    df_mes = df_reserva[mask]

    col_g1, col_g2 = st.columns([2, 1])

    with col_g1:
        st.write(f"### Evolução em {mes_sel}")
        if not df_mes.empty:
            df_evol = df_mes.groupby(['data_vencimento', 'tipo'])['valor'].sum().reset_index()
            fig_line = px.line(df_evol, x='data_vencimento', y='valor', color='tipo',
                               markers=True, color_discrete_map={"Receita": "#28a745", "Despesa": "#dc3545"})
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Sem lançamentos neste mês.")

    with col_g2:
        st.write("### 🚩 Top 5 Despesas")
        top_5 = df_mes[df_mes['tipo'] == "Despesa"].nlargest(5, 'valor')
        if not top_5.empty:
            for _, row in top_5.iterrows():
                st.warning(f"**R$ {row['valor']:,.2f}** - {row['descricao']}")
        else:
            st.write("Nenhuma despesa.")

    st.write("---")

    # --- GRÁFICO DE PIZZA ---
    if not df_mes.empty:
        st.write("### Distribuição por Categoria")
        fig_pizza = px.pie(df_mes[df_mes['tipo'] == 'Despesa'], values='valor', names='categoria', hole=0.4)
        st.plotly_chart(fig_pizza, use_container_width=True)