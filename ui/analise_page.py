import streamlit as st
import pandas as pd
import json
import calendar
from datetime import datetime
from services.database import Database
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


def analise_categorias_page(df_ignorar, df_saldos=None):
    df = Database.carregar_dados()

    # --- STYLE ENGINE: GLASSMORPHISM LUXURY ALTO CONTRASTE ---
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;800&display=swap');

        .main-header {
            font-family: 'Inter', sans-serif;
            padding: 15px 0 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 25px;
        }

        .title-main {
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            color: #ffffff !important;
            margin-bottom: 0px;
            text-transform: uppercase;
        }

        .subtitle-main {
            font-size: 0.85rem;
            font-weight: 600;
            color: #38bdf8 !important;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        .accent-line {
            width: 50px;
            height: 4px;
            background: #38bdf8;
            border-radius: 10px;
            margin-top: 10px;
        }

        .dashboard-container { display: flex; flex-wrap: wrap; gap: 15px; justify-content: space-between; margin-bottom: 20px; }
        .card-modern {
            flex: 1; min-width: 250px; padding: 22px; border-radius: 16px;
            background: #151d2e;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            color: #ffffff; transition: all 0.25s ease-in-out;
        }
        .card-modern:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
            border-color: rgba(56, 189, 248, 0.4);
        }
        .label-modern { font-size: 0.78rem; text-transform: uppercase; color: #cbd5e1; letter-spacing: 1px; font-weight: 600; }
        .value-modern { font-size: 1.7rem; font-weight: 800; margin: 8px 0; color: #ffffff !important; }
        .sub-value-modern { font-size: 0.85rem; color: #94a3b8; font-weight: 500; }
        .bg-blue { background: linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(15, 23, 42, 0.8)); border-top: 4px solid #38bdf8; }
        .bg-green { background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(15, 23, 42, 0.8)); border-top: 4px solid #22c55e; }
        .bg-red { background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(15, 23, 42, 0.8)); border-top: 4px solid #ef4444; }
        .bg-yellow { background: linear-gradient(135deg, rgba(234, 179, 8, 0.15), rgba(15, 23, 42, 0.8)); border-top: 4px solid #eab308; }
        .bg-dark { background: #151d2e; border-top: 4px solid #94a3b8; }
        .status-badge-modern { font-size: 0.78rem; font-weight: 700; padding: 5px 14px; border-radius: 50px; display: inline-block; margin-top: 6px; }
        .badge-alert { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
        .badge-ok { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }
    </style>

    <div class="main-header">
        <div class="subtitle-main">Insights & Performance</div>
        <div class="title-main">Inteligência Financeira</div>
        <div class="subtitle-main" style="color: #94a3b8 !important; letter-spacing: 1px; margin-top: 4px;">
            PlanejAI <span style="color: #38bdf8; font-weight: bold;">v1.0</span>
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
    ultimo_dia = calendar.monthrange(a_sel, m_sel)[1]
    data_corte = pd.Timestamp(datetime(a_sel, m_sel, ultimo_dia)).normalize()

    df['data_vencimento'] = pd.to_datetime(df['data_vencimento']).dt.normalize()
    hoje = pd.Timestamp(datetime.now().date()).normalize()

    # --- 2. CÁLCULO DE SALDO ASSERTIVO (H8.1 - CUMULATIVO ATÉ O MÊS) ---
    saldo_atual_real = df_saldos['valor'].sum() if (df_saldos is not None and not df_saldos.empty) else 0.0

    # Filtro: Tudo que está pendente/atrasado ATÉ o final do mês selecionado
    mask_pendente = (df['data_vencimento'] <= data_corte) & (df['status'] != "🟢 Concluído")

    receber_total = df[mask_pendente & (df['tipo'] == "Receita")]['valor'].sum()
    pagar_total = df[mask_pendente & (df['tipo'] == "Despesa")]['valor'].sum()

    saldo_projetado = saldo_atual_real + (receber_total - pagar_total)

    # Dados específicos do mês para os cards de performance
    df_mes = df[(df['data_vencimento'].dt.month == m_sel) & (df['data_vencimento'].dt.year == a_sel)].copy()

    if df_mes.empty:
        st.info(f"Nenhum lançamento encontrado para {mes_selecionado}.")
        st.markdown(f"""
        <div class="dashboard-container">
            <div class="card-modern bg-blue">
                <div class="label-modern">Saldo Projetado Final 🎯</div>
                <div class="value-modern">R$ {saldo_projetado:,.2f}</div>
                <div class="sub-value-modern">Acumulado até {mes_selecionado}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Cálculos de eficiência do mês
    receita_total_mes = df_mes[df_mes['tipo'] == "Receita"]['valor'].sum()
    despesa_total_mes = df_mes[df_mes['tipo'] == "Despesa"]['valor'].sum()
    eficiencia = (despesa_total_mes / receita_total_mes * 100) if receita_total_mes > 0 else 0

    st.markdown(f"### 🛡️ Potencial de Reserva {mes_selecionado}")

    if eficiencia > 90:
        st.markdown(f"""
            <div style="padding: 15px; background: rgba(239, 68, 68, 0.15); border-left: 5px solid #ef4444; border-radius: 10px; margin-bottom: 20px; color: #fca5a5; font-weight: 600;">
                ⚠️ <b>Atenção:</b> Comprometimento crítico de {eficiencia:.1f}% da renda em {mes_selecionado}!
            </div>
        """, unsafe_allow_html=True)

    # LINHA 1: CARDS DE PERFORMANCE
    st.markdown(f"""
    <div class="dashboard-container">
        <div class="card-modern bg-blue">
            <div class="label-modern">Saldo Projetado Final 🎯</div>
            <div class="value-modern">R$ {saldo_projetado:,.2f}</div>
            <div class="sub-value-modern">Considerando pendências até {mes_selecionado}</div>
        </div>
        <div class="card-modern {'bg-red' if eficiencia > 90 else 'bg-green'}">
            <div class="label-modern">Margem de Aporte</div>
            <div class="value-modern">{max(0, 100 - eficiencia):.1f}%</div>
            <div class="status-badge-modern {'badge-alert' if eficiencia > 90 else 'badge-ok'}">
                {'Risco Alto' if eficiencia > 90 else 'Capacidade Ideal'}
            </div>
        </div>
        <div class="card-modern bg-dark">
            <div class="label-modern">Eficiência ({mes_selecionado})</div>
            <div class="value-modern">{eficiencia:.1f}%</div>
            <div class="sub-value-modern">Meta: &lt; 70%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(max(0.0, min(eficiencia / 100, 1.0)))

    st.write("")

    # --- 3. SAÚDE DO FLUXO DE CAIXA ---
    st.subheader("🕒 Dinâmica de Pagamentos")
    despesas_contexto = df_mes[df_mes['tipo'] == "Despesa"].copy()

    mask_pago = despesas_contexto['status'].str.contains('Concluído|Pago|🟢', case=False, na=False)
    mask_atrasado = (~mask_pago) & (despesas_contexto['data_vencimento'] < hoje)

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

    if despesa_total_mes > 0:
        p_pago = (pago / despesa_total_mes * 100)
        p_pend = (pendente / despesa_total_mes * 100)
        p_atra = (atrasado / despesa_total_mes * 100)

        st.markdown(f"""
                <div style="display: flex; width: 100%; height: 10px; border-radius: 5px; overflow: hidden; background-color: rgba(255,255,255,0.08); margin-top: 10px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.12);">
                    <div style="width: {p_pago}%; background: linear-gradient(90deg, #22c55e, #16a34a); transition: width 0.5s ease;"></div>
                    <div style="width: {p_pend}%; background: linear-gradient(90deg, #eab308, #ca8a04); transition: width 0.5s ease;"></div>
                    <div style="width: {p_atra}%; background: linear-gradient(90deg, #ef4444, #dc2626); transition: width 0.5s ease;"></div>
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
                    As barras mostram o gasto total por categoria. A linha azul representa o impacto acumulado. 
                    💡 **Dica:** Foque em reduzir os primeiros itens da lista, pois representam a maior parte do seu custo.
                """)
