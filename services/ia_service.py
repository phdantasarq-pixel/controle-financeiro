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

    def gerar_insight(self, contexto: dict, mes_atual: str):
        """
        Recebe um dicionário com 'lancamentos' e 'saldos' e gera uma análise estratégica.
        """
        if not self.model:
            return "O cérebro da IA não está disponível no momento."

        # 1. Preparação dos dados de Lançamentos
        df_l = contexto.get("lancamentos", pd.DataFrame())
        df_l_limpo = df_l.copy()
        cols_drop = [c for c in ['_id', 'id', 'data_registro'] if c in df_l_limpo.columns]
        df_l_limpo = df_l_limpo.drop(columns=cols_drop)

        # 2. Preparação dos dados de Saldos Gerais (H7.1)
        df_s = contexto.get("saldos", pd.DataFrame())
        saldos_str = df_s.to_csv(index=False) if not df_s.empty else "Nenhum saldo informado."

        # 3. Construção do Prompt Estratégico
        prompt = f"""
        Você é o Consultor Estratégico do PlanejAI. Sua missão é analisar a saúde financeira do usuário.

        DATA ATUAL DE REFERÊNCIA: {mes_atual}

        ### DADOS DE SALDOS (O que o usuário POSSUI em conta/mãos):
        {saldos_str}

        ### DADOS DE LANÇAMENTOS (O que o usuário MOVIMENTOU):
        {df_l_limpo.to_csv(index=False)}

        Sua análise deve seguir estas diretrizes:
        1. Resuma o 'Poder de Fogo' (Total de Saldos vs Total de Despesas do mês).
        2. Identifique se o usuário está 'no azul' ou se as reservas estão diminuindo.
        3. Dê uma dica prática baseada na categoria onde ele mais gasta.
        4. Seja direto, use bullet points e mantenha um tom encorajador.
        5. Se o saldo for alto em relação aos gastos, sugira investir. Se for baixo, sugira cortes.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro na análise estratégica: {str(e)}"

    # Adicione este método dentro da classe IAService

    def chat(self, mensagem_usuario, contexto, historico_mensagens):
        if not self.model:
            return "IA indisponível."

        # Preparamos os dados para a IA saber do que estamos falando
        df_l = contexto.get("lancamentos", pd.DataFrame())
        df_s = contexto.get("saldos", pd.DataFrame())

        # Criamos a "memória" de curto prazo para este chat específico
        instrucao_sistema = f"""
        Você é o chat de consultoria do PlanejAI. 
        Dados do usuário:
        Saldos: {df_s.to_dict('records')}
        Últimos Gastos: {df_l.tail(10).to_dict('records')}

        Responda de forma humana, curta e prática.
        """

        try:
            # Iniciamos o chat com o histórico e a instrução de sistema
            chat_session = self.model.start_chat(history=[])  # O Streamlit já gerencia o histórico
            full_prompt = f"{instrucao_sistema}\n\nUsuário: {mensagem_usuario}"

            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Erro ao processar chat: {str(e)}"