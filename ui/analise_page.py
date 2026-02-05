import streamlit as st
import pandas as pd
import json
from datetime import datetime
from domain.analise import (
    calcular_pareto_categorias,
    gerar_grafico_pareto
)


def processar_dados_detalhados(df_original):
    if df_original.empty:
        return df_original
    df_analise = df_original.copy()
    registros_expandidos = []
    indices_para_remover = []

    for idx, row in df_analise.iterrows():
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
        elif row['categoria'] == "Cartão de Crédito":
            indices_para_remover.append(idx)

    df_analise = df_analise.drop(indices_para_remover)
    if registros_expandidos:
        df_analise = pd.concat([df_analise, pd.DataFrame(registros_expandidos)], ignore_index=True)
    return df_analise


def analise_categorias_page(df, df_saldos=None):
    st.header("🎯 Inteligência Financeira")

    if df.empty:
        st.warning("Sem dados suficientes para análise.")
        return

    # --- 1. CONFIGURAÇÃO DE TEMPO E SELETOR ---
    df['data_vencimento'] = pd.to_datetime(df['data_vencimento']).dt.normalize()
    hoje = pd.Timestamp(datetime.now().date()).normalize()

    # Criar opções de meses baseadas nos dados existentes
    df['mes_ano_ref'] = df['data_vencimento'].dt.strftime('%m/%Y')
    opcoes_meses = sorted(df['mes_ano_ref'].unique(),
                          key=lambda x: datetime.strptime(x, '%m/%Y'),
                          reverse=True)

    mes_atual_str = hoje.strftime('%m/%Y')
    if mes_atual_str not in opcoes_meses:
        opcoes_meses.insert(0, mes_atual_str)

    # Componente de Filtro Simples
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        mes_selecionado = st.selectbox("📅 Mês de Referência", options=opcoes_meses,
                                       index=opcoes_meses.index(mes_atual_str) if mes_atual_str in opcoes_meses else 0)

    # Base filtrada pelo seletor
    df_mes = df[df['mes_ano_ref'] == mes_selecionado].copy()

    st.write(f"Análise de eficiência e saúde circulatória de **{mes_selecionado}**.")

    if df_mes.empty:
        st.info(f"Nenhum lançamento encontrado para {mes_selecionado}.")
        return

    # --- 2. CÁLCULO DE SALDO (H8.1) ---
    saldo_total = df_saldos['valor'].sum() if df_saldos is not None else 1444.00

    # --- 3. POTENCIAL DE RESERVA ---
    receita_total = df_mes[df_mes['tipo'] == "Receita"]['valor'].sum()
    despesa_total_mes = df_mes[df_mes['tipo'] == "Despesa"]['valor'].sum()
    sobra_liquida = receita_total - despesa_total_mes
    eficiencia = (despesa_total_mes / receita_total * 100) if receita_total > 0 else 0

    with st.container(border=True):
        st.subheader(f"🛡️ Potencial de Reserva ({mes_selecionado})")
        if eficiencia > 90:
            st.error(f"⚠️ **Crítico:** Você comprometeu {eficiencia:.1f}% da renda de {mes_selecionado}!")

        c1, c2, c3 = st.columns(3)
        c1.metric("Sobra Estimada", f"R$ {sobra_liquida:,.2f}", delta=f"Saldo Real: R$ {saldo_total:,.2f}")
        c2.metric("Capacidade de Aporte", f"{max(0, 100 - eficiencia):.1f}%")
        c3.metric("Eficiência de Gastos", f"{eficiencia:.1f}%", delta="Meta: < 70%", delta_color="inverse")
        st.progress(max(0.0, min(eficiencia / 100, 1.0)))

    st.divider()

    # --- 4. SAÚDE DO FLUXO DE CAIXA (LÓGICA DE ATRASO AUTOMÁTICO) ---
    st.subheader("🕒 Saúde do Fluxo de Caixa")

    despesas_contexto = df_mes[df_mes['tipo'] == "Despesa"].copy()

    # 🟢 PAGO: Status contém "Concluído" ou "Pago"
    mask_pago = despesas_contexto['status'].str.contains('Concluído|Pago', case=False, na=False)

    # 🔴 EM ATRASO: (Status diz que está atrasado) OU (Data de vencimento < Hoje E não está pago)
    mask_atrasado = (
            (despesas_contexto['status'].str.contains('Atrasado|Vencido', case=False, na=False)) |
            ((despesas_contexto['data_vencimento'] < hoje) & (~mask_pago))
    )

    pago = despesas_contexto[mask_pago]['valor'].sum()
    atrasado = despesas_contexto[mask_atrasado]['valor'].sum()
    pendente = despesa_total_mes - pago - atrasado

    col1, col2, col3 = st.columns(3)
    with col1:
        st.success(f"**Liquidado**\nR$ {pago:,.2f}")
        pct_pago = (pago / despesa_total_mes * 100) if despesa_total_mes > 0 else 0
        st.caption(f"{pct_pago:.1f}% concluído")
    with col2:
        st.warning(f"**A Pagar**\nR$ {pendente:,.2f}")
        st.caption("Aguardando vencimento")
    with col3:
        if atrasado > 0:
            st.error(f"**Em Atraso**\nR$ {atrasado:,.2f}")
            st.caption("Risco de juros e multas")
        else:
            st.info(f"**Em Atraso**\nR$ 0.00")
            st.caption("Tudo em dia!")

    if despesa_total_mes > 0:
        st.write("**Distribuição do Fluxo:**")
        p_pago = (pago / despesa_total_mes) * 100
        p_pend = (pendente / despesa_total_mes) * 100
        p_atra = (atrasado / despesa_total_mes) * 100
        st.markdown(f"""
            <div style="display: flex; width: 100%; height: 20px; border-radius: 10px; overflow: hidden; background-color: #eee;">
                <div style="width: {p_pago}%; background-color: #28a745;"></div>
                <div style="width: {p_pend}%; background-color: #ffc107;"></div>
                <div style="width: {p_atra}%; background-color: #dc3545;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 5px; color: gray;">
                <span>Concluído: {p_pago:.1f}%</span>
                <span>Pendente: {p_pend:.1f}%</span>
                <span>Atrasado: {p_atra:.1f}%</span>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- 5. ANÁLISE DE PARETO ---
    st.subheader(f"📊 Onde está o seu dinheiro? (Pareto - {mes_selecionado})")
    df_expandido = processar_dados_detalhados(df_mes)
    df_pareto = calcular_pareto_categorias(df_expandido)

    if df_pareto is not None and not df_pareto.empty:
        viloes = df_pareto[df_pareto['acumulado'] <= 90]['categoria'].tolist()
        c_graf, c_viloes = st.columns([2, 1])
        with c_graf:
            st.plotly_chart(gerar_grafico_pareto(df_pareto), use_container_width=True)
        with c_viloes:
            st.markdown("### 🕵️ Os Vilões")
            viloes_limpos = [c for c in viloes if c != "Cartão de Crédito"]
            for i, cat in enumerate(viloes_limpos):
                st.error(f"{i + 1}º - {cat}")
            st.markdown("---")
            st.caption("""
                                **Como ler este gráfico:**
                                As barras mostram o gasto total por categoria. A linha vermelha 
                                representa o impacto acumulado. 

                                💡 **Dica:** Foque em reduzir os primeiros itens da lista (os vilões), 
                                pois eles representam ~80% do seu custo mensal.
                            """)

            st.info("🔍 Detalhamento de Itens das Faturas (IA)")