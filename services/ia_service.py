import google.generativeai as genai
import streamlit as st
import pandas as pd


class IAService:
    def __init__(self):
        self.api_key = st.secrets.get("GEMINI_API_KEY")
        self.model = None

        if not self.api_key:
            st.error("Chave da API não encontrada nos Secrets.")
            return

        try:
            genai.configure(api_key=self.api_key)
            available_models = [m.name for m in genai.list_models() if
                                'generateContent' in m.supported_generation_methods]

            preferencia = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
            modelo_escolhido = next((p for p in preferencia if p in available_models),
                                    available_models[0] if available_models else None)

            if modelo_escolhido:
                self.model = genai.GenerativeModel(modelo_escolhido)
            else:
                st.error("Nenhum modelo compatível encontrado.")
        except Exception as e:
            st.error(f"Erro ao inicializar IA: {e}")

    def gerar_insight(self, contexto: dict, mes_atual: str, indicadores: dict = None):
        """
        Gera análise estratégica baseada em lançamentos, saldos reais e indicadores calculados.
        """
        if not self.model:
            return "O cérebro da IA não está disponível no momento."

        # Preparação dos dados
        df_l = contexto.get("lancamentos", pd.DataFrame())
        df_l_limpo = df_l.copy()
        cols_drop = [c for c in ['_id', 'id', 'data_registro'] if c in df_l_limpo.columns]
        df_l_limpo = df_l_limpo.drop(columns=cols_drop)

        df_s = contexto.get("saldos", pd.DataFrame())
        saldos_str = df_s.to_csv(index=False) if not df_s.empty else "Nenhum saldo informado."

        # Injeção de indicadores calculados para precisão matemática [H8.1]
        txt_indicadores = ""
        if indicadores:
            txt_indicadores = f"""
            ### INDICADORES FINANCEIROS (VALORES REAIS CALCULADOS):
            - Saldo Real em Contas Hoje: R$ {indicadores.get('saldo_contas', 0):,.2f}
            - Saldo Livre Projetado (Fim do Mês): R$ {indicadores.get('saldo_projetado', 0):,.2f}
            - Balanço Líquido do Mês Selecionado: R$ {indicadores.get('balanco', 0):,.2f}
            """

        prompt = f"""
        Você é o Consultor Estratégico do PlanejAI. Analise a saúde financeira com foco no FLUXO DE CAIXA.

        DATA ATUAL DE REFERÊNCIA: {mes_atual}

        {txt_indicadores}

        ### DADOS DE SALDOS BANCÁRIOS:
        {saldos_str}

        ### LISTA DE LANÇAMENTOS (Últimas movimentações):
        {df_l_limpo.tail(50).to_csv(index=False)}

        Sua análise deve:
        1. Validar se o 'Saldo Livre Projetado' é suficiente para as despesas futuras.
        2. Alertar se o usuário está gastando mais do que recebe no mês (Balanço Negativo).
        3. Se o Saldo Livre for negativo, sugira onde cortar baseado nos lançamentos.
        4. Use bullet points e seja muito direto e encorajador.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro na análise estratégica: {str(e)}"

    def chat(self, mensagem_usuario, contexto, historico_mensagens, indicadores: dict = None):
        if not self.model:
            return "IA indisponível."

        df_l = contexto.get("lancamentos", pd.DataFrame())
        df_s = contexto.get("saldos", pd.DataFrame())

        info_financeira = f"Saldos: {df_s.to_dict('records')}"
        if indicadores:
            info_financeira += f" | Saldo Projetado Fim do Mês: R$ {indicadores.get('saldo_projetado', 0):,.2f}"

        instrucao_sistema = f"""
        Você é o consultor do PlanejAI. 
        Contexto financeiro: {info_financeira}
        Responda de forma humana, curta e prática. Sempre considere o 'Saldo Projetado' para dizer se o usuário pode ou não gastar com algo.
        """

        try:
            full_prompt = f"{instrucao_sistema}\n\nUsuário: {mensagem_usuario}"
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Erro ao processar chat: {str(e)}"