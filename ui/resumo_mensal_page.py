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
        if not sucesso_expansao and row['categoria'] != "Cartão de Crédito":
            registros.append({"valor": row['valor'], "categoria": row['categoria'], "descricao": row['descricao']})
    return pd.DataFrame(registros) if registros else pd.DataFrame(columns=["valor", "categoria", "descricao"])


def resumo_mensal_page(df):
    # --- CABEÇALHO MODERNIZADO (LUXURY STYLE - ALTO CONTRASTE) ---
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
                color: #FFFFFF !important;
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
        </style>

        <div class="main-header">
            <div class="subtitle-main">Cockpit de Gestão</div>
            <div class="title-main">Resumo Mensal</div>
            <div class="subtitle-main" style="color: #94a3b8 !important; letter-spacing: 1px; margin-top: 4px;">
                PlanejAI <span style="color: #38bdf8; font-weight: bold;">v1.0</span>
            </div>
            <div class="accent-line"></div>
        </div>
    """, unsafe_allow_html=True)

    # --- STYLE ENGINE: GLASSMORPHISM + ALTO CONTRASTE ---
    st.markdown("""
    <style>
        .dashboard-container { display: flex; flex-wrap: wrap; gap: 15px; justify-content: space-between; margin-bottom: 20px; }
        .card-modern {
            flex: 1; min-width: 220px; padding: 22px; border-radius: 16px;
            background: #151d2e;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            color: #ffffff;
            transition: all 0.25s ease-in-out;
        }
        .card-modern:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
            border-color: rgba(56, 189, 248, 0.4);
        }
        .label { font-size: 0.78rem; text-transform: uppercase; color: #cbd5e1; letter-spacing: 1px; font-weight: 600; }
        .value { font-size: 1.7rem; font-weight: 800; margin: 8px 0; color: #ffffff !important; }
        .status { font-size: 0.8rem; font-weight: 700; padding: 5px 12px; border-radius: 50px; display: inline-block; }

        .bg-saldo { background: linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(15, 23, 42, 0.8)); border-top: 4px solid #38bdf8; }
        .bg-receita { background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(15, 23, 42, 0.8)); border-top: 4px solid #22c55e; }
        .bg-despesa { background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(15, 23, 42, 0.8)); border-top: 4px solid #ef4444; }
        .bg-resultado { background: linear-gradient(135deg, rgba(234, 179, 8, 0.15), rgba(15, 23, 42, 0.8)); border-top: 4px solid #eab308; }
        .bg-comprometimento { background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(15, 23, 42, 0.8)); border-top: 4px solid #6366f1; }

        .status-ok { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }
        .status-alert { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
    </style>
    """, unsafe_allow_html=True)

    # --- LÓGICA DE DADOS ---
    mes_sel = seletor_meses_inteligente(key_suffix="resumo_geral")
    mes_f, ano_f = map(int, mes_sel.split('/'))
    df_mes = df[(pd.to_datetime(df['data_vencimento']).dt.month == mes_f) & (
                pd.to_datetime(df['data_vencimento']).dt.year == ano_f)].copy()

    receitas_mes = df_mes[df_mes['tipo'] == "Receita"]['valor'].sum()
    total_despesas_mes = df_mes[df_mes['tipo'] == "Despesa"]['valor'].sum()
    resultado_mes = receitas_mes - total_despesas_mes
    saldo_atual = Database.obter_total_saldos_real()
    fixos = df_mes[(df_mes['tipo'] == "Despesa") & (df_mes['natureza'] == "Fixo")]['valor'].sum()
    variaveis = df_mes[(df_mes['tipo'] == "Despesa") & (df_mes['natureza'] == "Variável")]['valor'].sum()
    comprometimento = (total_despesas_mes / receitas_mes * 100) if receitas_mes > 0 else 0

    # --- LINHA 1: MÉTRICAS ---
    st.markdown(f"""
    <div class="dashboard-container">
        <div class="card-modern bg-saldo">
            <div class="label">Saldo em Contas 🏦</div>
            <div class="value">R$ {saldo_atual:,.2f}</div>
            <div class="status status-ok">Disponível Real</div>
        </div>
        <div class="card-modern bg-receita">
            <div class="label">Entradas (Mês) 📈</div>
            <div class="value">R$ {receitas_mes:,.2f}</div>
            <div class="status status-ok">Total Créditos</div>
        </div>
        <div class="card-modern bg-despesa">
            <div class="label">Saídas (Mês) 📉</div>
            <div class="value">R$ {total_despesas_mes:,.2f}</div>
            <div class="status status-alert">Total Débitos</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- LINHA 2: PERFORMANCE ---
    st.markdown(f"""
    <div class="dashboard-container">
        <div class="card-modern bg-resultado">
            <div class="label">Resultado Mensal ⚖️</div>
            <div class="value">R$ {resultado_mes:,.2f}</div>
            <div class="status {'status-ok' if resultado_mes >= 0 else 'status-alert'}">
                {'🟢 Superávit' if resultado_mes >= 0 else '🔴 Déficit'}
            </div>
        </div>
        <div class="card-modern bg-comprometimento">
            <div class="label">Comprometimento 🚨</div>
            <div class="value">{comprometimento:.1f}%</div>
            <div class="status {'status-ok' if comprometimento < 70 else 'status-alert'}">
                {'Saudável' if comprometimento < 70 else 'Cuidado!'}
            </div>
        </div>
        <div class="card-modern" style="background: #151d2e; border-top: 4px solid #a855f7;">
            <div class="label">Divisão de Custos 📊</div>
            <div style="margin-top:10px; font-size: 0.95rem; color: #f1f5f9;">
                📌 Fixos: <b style="color: #ffffff;">R$ {fixos:,.2f}</b><br>
                💸 Variáveis: <b style="color: #ffffff;">R$ {variaveis:,.2f}</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- LINHA 3: GRÁFICOS (PIZZA E ÁREA) ---
    col_pizza, col_area = st.columns(2)

    with col_pizza:
        with st.container(border=True):
            st.markdown("**🍕 Despesas por Categoria**")
            df_analise = processar_dados_detalhados_resumo(df_mes[df_mes['tipo'] == "Despesa"])
            if not df_analise.empty:
                fig_pizza = px.pie(df_analise, values='valor', names='categoria', hole=0.4,
                                   color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pizza.update_layout(
                    height=300, 
                    showlegend=False, 
                    margin=dict(t=10, b=10, l=10, r=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    template="plotly_dark",
                    font=dict(color="#F8FAFC")
                )
                st.plotly_chart(fig_pizza, use_container_width=True)

    with col_area:
        with st.container(border=True):
            st.markdown("**📅 Fluxo de Caixa Diário**")
            df_daily = df_mes[df_mes['tipo'] == "Despesa"].groupby(pd.to_datetime(df_mes['data_vencimento']).dt.day)[
                'valor'].sum().reset_index()
            fig_area = px.area(df_daily, x='data_vencimento', y='valor', color_discrete_sequence=['#ef4444'])
            fig_area.update_layout(
                height=300, 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                template="plotly_dark",
                font=dict(color="#F8FAFC"),
                margin=dict(t=10, l=10, r=10, b=10)
            )
            st.plotly_chart(fig_area, use_container_width=True)

    # --- LINHA 4: Desembolsos Detalhados ---
    st.markdown("**🏆 Top 5 Desembolsos Detalhados**")
    if not df_analise.empty:
        top5 = df_analise.sort_values(by='valor', ascending=False).head(5)

        with st.container():
            for _, row in top5.iterrows():
                st.markdown(f"""
                    <div class="card-modern" style="
                        display: flex; 
                        justify-content: space-between; 
                        align-items: center; 
                        padding: 14px 20px; 
                        margin-bottom: 8px; 
                        border-left: 4px solid #ef4444; 
                        border-bottom: none;
                        min-width: 100%;
                    ">
                        <div style="flex: 2;">
                            <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600;">{row['categoria']}</div>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #ffffff;">{row['descricao']}</div>
                        </div>
                        <div style="flex: 1; text-align: right;">
                            <div style="color: #f87171; font-weight: 800; font-size: 1.15rem;">
                                R$ {row['valor']:,.2f}
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Nenhum dado detalhado disponível para este período.")
