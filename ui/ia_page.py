import streamlit as st
from services.ia_service import IAService
from services.database import Database
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import io


# --- FUNÇÃO AUXILIAR PARA PDF COM GRÁFICOS ---
def gerar_pdf_completo(mensagens, indicadores, insight_ia, df_mensal):
    pdf = FPDF()
    pdf.add_page()

    # Header Estilo Luxury
    pdf.set_fill_color(20, 20, 20)
    pdf.rect(0, 0, 210, 45, 'F')

    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "PLANEJAI - CONSULTORIA ESTRATEGICA", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, f"Relatorio v8.1 | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')

    pdf.ln(25)
    pdf.set_text_color(40, 40, 40)

    # 1. Indicadores Financeiros
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Resumo Financeiro Atual", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"- Saldo em Contas: R$ {indicadores['saldo_contas']:,.2f}", ln=True)
    pdf.cell(0, 8, f"- Saldo Projetado: R$ {indicadores['saldo_projetado']:,.2f}", ln=True)
    pdf.cell(0, 8, f"- Balanco do Mes: R$ {indicadores['balanco']:,.2f}", ln=True)

    # 2. Gráfico de Composição (Matplotlib)
    if not df_mensal.empty:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "2. Composicao de Fluxo", ln=True)

        # Gerar gráfico em memória
        totais = df_mensal.groupby('tipo')['valor'].sum()
        fig, ax = plt.subplots(figsize=(6, 4))
        # Cores: Verde para Receita, Vermelho para Despesa
        cores = ['#e74c3c' if x == 'Despesa' else '#2ecc71' for x in totais.index]

        ax.pie(totais, labels=totais.index, autopct='%1.1f%%', startangle=140, colors=cores,
               wedgeprops={'edgecolor': 'white'})
        ax.set_title("Distribuicao Receitas vs Despesas", fontsize=12, pad=20)

        # Salvar em buffer
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=150)
        img_buf.seek(0)

        # Inserir no PDF
        pdf.image(img_buf, x=55, y=pdf.get_y(), w=100)
        pdf.ln(75)  # Espaço para o gráfico
        plt.close(fig)

    # 3. Insight da IA
    if insight_ia:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "3. Analise Estrategica (Cerebro PlanejAI)", ln=True)
        pdf.set_font("Arial", size=10)
        texto_limpo = str(insight_ia).encode('latin-1', 'ignore').decode('latin-1')
        pdf.multi_cell(0, 7, texto_limpo)

    # 4. Histórico do Chat
    if mensagens:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "4. Historico da Sessao", ln=True)
        pdf.ln(5)
        for msg in mensagens:
            role = "USUARIO" if msg['role'] == "user" else "PLANEJAI"
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(0, 7, f"[{role}]:", ln=True)
            pdf.set_font("Arial", size=9)
            msg_limpa = str(msg['content']).encode('latin-1', 'ignore').decode('latin-1')
            pdf.multi_cell(0, 5, msg_limpa)
            pdf.ln(3)

    return bytes(pdf.output())


# --- PÁGINA PRINCIPAL ---
def ia_page(df_lancamentos):
    # CSS Luxury (Mantido conforme solicitado)
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
            .main-header { font-family: 'Inter', sans-serif; margin-bottom: 25px; }
            .title-main {
                font-size: 2rem; font-weight: 800; letter-spacing: -1px;
                background: linear-gradient(90deg, #FFFFFF 0%, #A0A0A0 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                margin-bottom: 0px; text-transform: uppercase;
            }
            .subtitle-main {
                font-size: 0.8rem; font-weight: 300; color: #3498db;
                letter-spacing: 2px; text-transform: uppercase;
            }
            .stChatMessage {
                background: rgba(255, 255, 255, 0.03) !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                border-radius: 15px !important;
                margin-bottom: 10px;
            }
            .insight-card {
                background: rgba(52, 152, 219, 0.05);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(52, 152, 219, 0.2);
                margin-bottom: 25px;
            }
        </style>

        <div class="main-header">
            <div class="subtitle-main">Consultoria Inteligente</div>
            <div class="title-main">Cérebro PlanejAI</div>
            <div class="subtitle-main" style="color: rgba(255,255,255,0.4); letter-spacing: 1px; margin-top: 5px;">
                Tecnologia <span style="color: #3498db; font-weight: bold;">v8.1</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 1. CÁLCULO DE INDICADORES
    saldo_atual_contas = Database.obter_total_saldos_real()
    df_p = df_lancamentos.copy()
    df_p['data_vencimento'] = pd.to_datetime(df_p['data_vencimento'], errors='coerce')
    hoje = datetime.now()

    df_atual = df_p[(df_p['data_vencimento'].dt.month == hoje.month) &
                    (df_p['data_vencimento'].dt.year == hoje.year)].copy()

    rec_pend_atual = df_atual[(df_atual['tipo'] == "Receita") & (df_atual['status'] != "Concluído")]['valor'].sum()
    desp_pend_atual = df_atual[(df_atual['tipo'] == "Despesa") & (df_atual['status'] != "Concluído")]['valor'].sum()

    saldo_fechamento_atual = saldo_atual_contas + rec_pend_atual - desp_pend_atual
    balanco_mensal = df_atual[df_atual['tipo'] == "Receita"]['valor'].sum() - df_atual[df_atual['tipo'] == "Despesa"][
        'valor'].sum()

    indicadores_ia = {
        "saldo_contas": saldo_atual_contas,
        "saldo_projetado": saldo_fechamento_atual,
        "balanco": balanco_mensal
    }

    # 2. CONTEXTO
    df_saldos = Database.carregar_saldos()
    contexto_completo = {"lancamentos": df_lancamentos, "saldos": df_saldos}

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "ultimo_insight" not in st.session_state:
        st.session_state.ultimo_insight = None

    # 3. CONTAINER DE INSIGHTS
    st.markdown('<div class="insight-card">', unsafe_allow_html=True)
    st.markdown("<p style='margin:0; font-weight:600;'>🎯 Insight Estratégico do Mês</p>", unsafe_allow_html=True)

    if st.button("✨ Gerar Análise de Fluxo", use_container_width=True, type="primary"):
        with st.spinner("IA processando fluxos de caixa..."):
            ai = IAService()
            st.session_state.ultimo_insight = ai.gerar_insight(contexto_completo, hoje.strftime("%m/%Y"),
                                                               indicadores=indicadores_ia)

    if st.session_state.ultimo_insight:
        st.info(st.session_state.ultimo_insight)
    st.markdown('</div>', unsafe_allow_html=True)

    # 4. ÁREA DO CHAT
    st.markdown("### 💬 Chat com o Consultor")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt_text := st.chat_input("Ex: Qual meu impacto financeiro se eu comprar um carro agora?",
                                    key="chat_input_planejai"):
        st.session_state.messages.append({"role": "user", "content": prompt_text})
        with st.chat_message("user"):
            st.markdown(prompt_text)

        with st.chat_message("assistant"):
            with st.spinner("Analisando dados..."):
                ai = IAService()
                resposta = ai.chat(prompt_text, contexto_completo, indicadores_ia)
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})
        st.rerun()

    # 5. EXPORTAÇÃO (PDF COM GRÁFICO)
    if st.session_state.messages or st.session_state.ultimo_insight:
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            try:
                # Agora gera com gráfico
                pdf_data = gerar_pdf_completo(
                    st.session_state.messages,
                    indicadores_ia,
                    st.session_state.ultimo_insight,
                    df_atual
                )

                st.download_button(
                    label="👑 Exportar Relatório PDF Profissional",
                    data=pdf_data,
                    file_name=f"relatorio_planejai_{hoje.strftime('%m_%y')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Erro ao incluir gráficos: {e}")

        with col2:
            chat_txt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button(
                label="📄 Exportar Conversa (TXT)",
                data=chat_txt,
                file_name=f"conversa_planejai.txt",
                mime="text/plain",
                use_container_width=True
            )