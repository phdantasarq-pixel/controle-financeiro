import streamlit as st
import pandas as pd
import json
from datetime import datetime
from domain.analise import (
    calcular_pareto_categorias,
    gerar_grafico_pareto
)

# Tenta importar o componente padrão, se falhar mantém o fallback
try:
    from ui.components import seletor_meses_inteligente
except Exception:
    seletor_meses_inteligente = None

def processar_dados_detalhados(df_original):
    """Mantém a lógica de expansão de itens de IA para análise precisa"""
    if df_original.empty:
        return df_original
    df_analise = df_original.copy()
    registros_expandidos = []
    indices_para_remover = []

    for idx, row in df_analise.iterrows():
        # Verificação de detalhes da IA conforme alteração de subheader solicitada
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
        elif row.get('categoria') == "Cartão de Crédito":
            indices_para_remover.append(idx)

    df_analise = df_analise.drop(indices_para_remover)
    if registros_expandidos:
        df_analise = pd.concat([df_analise, pd.DataFrame(registros_expandidos)], ignore_index=True)
    return df_analise

def analise_categorias_page(df, df_saldos=None):
    # --- STYLE ENGINE: GLASSMORPHISM LUXURY ---
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;800&display=swap');

        .main-header {
            font-family: 'Inter', sans-serif;
            padding: 20px 0 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 30px;
        }

        .title-main {
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            background: linear-gradient(90deg, #FFFFFF 0%, #A0A0A0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
            text-transform: uppercase; /* Força Caixa Alta */
        }

        .subtitle-main {
            font-size: 0.85rem;
            font-weight: 300;
            color: #3498db;
            letter-spacing: 3px;
            text-transform: uppercase;
            opacity: 0.9;
        }

        .accent-line {
            width: 50px;
            height: 4px;
            background: #3498db;
            border-radius: 10px;
            margin-top: 15px;
        }

        .dashboard-container { display: flex; flex-wrap: wrap; gap: 15px; justify-content: space-between; margin-bottom: 20px; }
        .card-modern {
            flex: 1; min-width: 250px; padding: 22px; border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px);
            color: white; transition: all 0.3s ease-in-out;
        }
        .card-modern:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        .label-modern { font-size: 0.75rem; text-transform: uppercase; opacity: 0.8; letter-spacing: 1.5px; font-weight: 600; }
        .value-modern { font-size: 1.6rem; font-weight: 800; margin: 8px 0; }
        .sub-value-modern { font-size: 0.8rem; opacity: 0.6; }
        .bg-blue { background: linear-gradient(135deg, rgba(52, 152, 219, 0.15), rgba(44, 62, 80, 0.4)); border-top: 4px solid #3498db; }
        .bg-green { background: linear-gradient(135deg, rgba(46, 204, 113, 0.15), rgba(0, 0, 0, 0.4)); border-top: 4px solid #2ecc71; }
        .bg-red { background: linear-gradient(135deg, rgba(231, 76, 60, 0.15), rgba(0, 0, 0, 0.4)); border-top: 4px solid #e74c3c; }
        .bg-yellow { background: linear-gradient(135deg, rgba(241, 196, 15, 0.15), rgba(0, 0, 0, 0.4)); border-top: 4px solid #f1c40f; }
        .bg-dark { background: rgba(255, 255, 255, 0.05); border-top: 4px solid #95a5a6; }
        .status-badge-modern { font-size: 0.75rem; font-weight: 600; padding: 4px 12px; border-radius: 50px; display: inline-block; margin-top: 5px; }
        .badge-alert { background: rgba(231, 76, 60, 0.2); color: #e74c3c; }
        .badge-ok { background: rgba(46, 204, 113, 0.2); color: #2ecc71; }
    </style>

    <div class="main-header">
        <div class="subtitle-main">Insights & Performance</div>
        <div class="title-main">Inteligência Financeira</div>
        <div class="subtitle-main" style="color: rgba(255,255,255,0.4); letter-spacing: 1px; margin-top: 5px;">
            PlanejAI <span style="color: #3498db; font-weight: bold;">v8.1</span>
        </div>
        <div class="accent-line"></div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("Sem dados suficientes para análise.")
        return

    # --- 1. CONFIGURAÇÃO DE TEMPO ---
    if seletor_meses_inteligente:
        mes_selecionado = seletor_meses_inteligente(key_suffix="analise_ia_v8_modern")
    else:
        df['mes_ano_ref'] = pd.to_datetime(df['data_vencimento']).dt.strftime('%m/%Y')
        opcoes = sorted(df['mes_ano_ref'].unique(), reverse=True)
        mes_selecionado = st.selectbox("📅 Mês de Referência", options=opcoes)

    m_sel, a_sel = map(int, mes_selecionado.split("/"))
    df['data_vencimento'] = pd.to_datetime(df['data_vencimento']).dt.normalize()
    hoje = pd.Timestamp(datetime.now().date()).normalize()
    df_mes = df[(df['data_vencimento'].dt.month == m_sel) & (df['data_vencimento'].dt.year == a_sel)].copy()

    if df_mes.empty:
        st.info(f"Nenhum lançamento encontrado para {mes_selecionado}.")
        return

    # --- 2. CÁLCULO DE SALDO E PERFORMANCE (H8.1) ---
    saldo_atual_real = df_saldos['valor'].sum() if (df_saldos is not None and not df_saldos.empty) else 0.0
    receita_total = df_mes[df_mes['tipo'] == "Receita"]['valor'].sum()
    despesa_total_mes = df_mes[df_mes['tipo'] == "Despesa"]['valor'].sum()
    sobra_do_mes = receita_total - despesa_total_mes
    saldo_projetado = saldo_atual_real + sobra_do_mes
    eficiencia = (despesa_total_mes / receita_total * 100) if receita_total > 0 else 0

    st.markdown(f"### 🛡️ Potencial de Reserva {mes_selecionado}")

    if eficiencia > 90:
        st.markdown(f"""
            <div style="padding: 15px; background: rgba(231, 76, 60, 0.1); border-left: 5px solid #e74c3c; border-radius: 10px; margin-bottom: 20px; color: #ff4d4d;">
                ⚠️ <b>Atenção:</b> Comprometimento crítico de {eficiencia:.1f}% da renda!
            </div>
        """, unsafe_allow_html=True)

    # LINHA 1: CARDS DE PERFORMANCE
    st.markdown(f"""
    <div class="dashboard-container">
        <div class="card-modern bg-blue">
            <div class="label-modern">Saldo Projetado Final</div>
            <div class="value-modern">R$ {saldo_projetado:,.2f}</div>
            <div class="sub-value-modern">Saldo Atual em Conta: R$ {saldo_atual_real:,.2f}</div>
        </div>
        <div class="card-modern {'bg-red' if eficiencia > 90 else 'bg-green'}">
            <div class="label-modern">Margem de Aporte</div>
            <div class="value-modern">{max(0, 100 - eficiencia):.1f}%</div>
            <div class="status-badge-modern {'badge-alert' if eficiencia > 90 else 'badge-ok'}">
                {'Risco Alto' if eficiencia > 90 else 'Capacidade Ideal'}
            </div>
        </div>
        <div class="card-modern bg-dark">
            <div class="label-modern">Eficiência</div>
            <div class="value-modern">{eficiencia:.1f}%</div>
            <div class="sub-value-modern">Meta: < 70%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(max(0.0, min(eficiencia / 100, 1.0)))
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. SAÚDE DO FLUXO DE CAIXA ---
    st.subheader("🕒 Dinâmica de Pagamentos")
    despesas_contexto = df_mes[df_mes['tipo'] == "Despesa"].copy()
    mask_pago = despesas_contexto['status'].str.contains('Concluído|Pago|🟢', case=False, na=False)
    mask_atrasado = (despesas_contexto['status'].str.contains('Atrasado|Vencido|🔴', case=False, na=False)) | \
                    ((despesas_contexto['data_vencimento'] < hoje) & (~mask_pago))

    pago = despesas_contexto[mask_pago]['valor'].sum()
    atrasado = despesas_contexto[mask_atrasado]['valor'].sum()
    pendente = despesa_total_mes - pago - atrasado

    st.markdown(f"""
        <div class="dashboard-container">
            <div class="card-modern bg-green">
                <div class="label-modern">✅ Liquidado</div>
                <div class="value-modern">R$ {pago:,.2f}</div>
                <div class="sub-value-modern">{(pago / despesa_total_mes * 100 if despesa_total_mes > 0 else 0):.1f}% do mês</div>
            </div>
            <div class="card-modern bg-yellow">
                <div class="label-modern">⏳ A Pagar</div>
                <div class="value-modern">R$ {pendente:,.2f}</div>
                <div class="sub-value-modern">Aguardando data</div>
            </div>
            <div class="card-modern {'bg-red' if atrasado > 0 else 'bg-dark'}">
                <div class="label-modern">🚨 Em Atraso</div>
                <div class="value-modern">R$ {atrasado:,.2f}</div>
                <div class="sub-value-modern">{('Risco de juros' if atrasado > 0 else 'Tudo em dia')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # BARRA DE DISTRIBUIÇÃO VISUAL (RESTAURADA)
    if despesa_total_mes > 0:
        p_pago = (pago / despesa_total_mes * 100)
        p_pend = (pendente / despesa_total_mes * 100)
        p_atra = (atrasado / despesa_total_mes * 100)

        st.markdown(f"""
                <div style="display: flex; width: 100%; height: 10px; border-radius: 5px; overflow: hidden; background-color: rgba(255,255,255,0.05); margin-top: 10px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="width: {p_pago}%; background: linear-gradient(90deg, #2ecc71, #27ae60); transition: width 0.5s ease;"></div>
                    <div style="width: {p_pend}%; background: linear-gradient(90deg, #f1c40f, #f39c12); transition: width 0.5s ease;"></div>
                    <div style="width: {p_atra}%; background: linear-gradient(90deg, #e74c3c, #c0392b); transition: width 0.5s ease;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: -20px; margin-bottom: 20px;">
                    <span style="color: #2ecc71; font-size: 0.65rem; font-weight: bold;">{p_pago:.1f}%</span>
                    <span style="color: #f1c40f; font-size: 0.65rem; font-weight: bold;">{p_pend:.1f}%</span>
                    <span style="color: #e74c3c; font-size: 0.65rem; font-weight: bold;">{p_atra:.1f}%</span>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # --- 4. ANÁLISE DE PARETO ---
    st.subheader(f"📊 Curva de Pareto de Gastos")
    df_expandido = processar_dados_detalhados(df_mes)
    df_pareto = calcular_pareto_categorias(df_expandido)

    if df_pareto is not None and not df_pareto.empty:
        c_graf, c_viloes = st.columns([2, 1])
        with c_graf:
            st.plotly_chart(gerar_grafico_pareto(df_pareto), use_container_width=True)
        with c_viloes:
            st.markdown("### 🕵️ Principais Ofensores")
            viloes = df_pareto[df_pareto['acumulado'] <= 90]['categoria'].tolist()
            viloes_limpos = [c for c in viloes if c != "Cartão de Crédito"]

            for i, cat in enumerate(viloes_limpos[:5]):
                st.error(f"{i + 1}º - {cat}")

            with st.expander("💡 Como otimizar?"):
                st.caption("""
                    **Como ler este gráfico:**
                    As barras mostram o gasto total por categoria. A linha vermelha representa o impacto acumulado. 
                    💡 **Dica:** Foque em reduzir os primeiros itens da lista, pois representam a maior parte do seu custo.
                """)