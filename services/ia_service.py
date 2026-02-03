import google.generativeai as genai
import streamlit as st
import pandas as pd
import json
import os


class IAService:
    def __init__(self):
        # Tenta pegar dos secrets, se não existir, usa a chave que você forneceu
        self.api_key = st.secrets.get("GEMINI_API_KEY") or "AIzaSyCQs5I9EcncBWQrQFknYSd50LIXjSDsAGs"
        self.model = None

        if not self.api_key:
            st.error("Chave da API não configurada.")
            return

        try:
            genai.configure(api_key=self.api_key)

            # Lista modelos disponíveis para garantir o uso de um funcional
            available_models = [m.name for m in genai.list_models() if
                                'generateContent' in m.supported_generation_methods]

            # Prioridade para o 1.5-flash (mais rápido e barato para faturas)
            preferencia = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
            modelo_escolhido = next((p for p in preferencia if p in available_models),
                                    available_models[0] if available_models else None)

            if modelo_escolhido:
                self.model = genai.GenerativeModel(modelo_escolhido)
            else:
                st.error("Nenhum modelo compatível encontrado.")
        except Exception as e:
            st.error(f"Erro ao inicializar IA: {e}")

    def processar_fatura(self, arquivo):
        """
        Extrai dados de faturas (PDF ou Imagem), sanitiza nomes e categoriza.
        """
        if not self.model:
            st.error("Modelo de IA não carregado.")
            return []

        try:
            # Preparação dos dados do arquivo
            arquivo_bytes = arquivo.read()
            mime_type = arquivo.type

            # Reinicia o ponteiro do arquivo para caso seja lido novamente
            arquivo.seek(0)

            prompt = """
            Você é um especialista em análise de faturas de cartão de crédito do sistema PlanejAI.
            Extraia os itens desta fatura e transforme-os em dados limpos.

            DIRETRIZES:
            1. SANITIZAÇÃO: Remova códigos, números de parcelas ou caracteres especiais (ex: 'UBER *TRIP 123' -> 'Uber').
            2. CATEGORIZAÇÃO: Use EXATAMENTE uma destas: [Moradia, Alimentação, Transporte, Lazer, Saúde, Educação, Assinaturas, Cartão de Crédito, Outro].
            3. VALOR: Extraia apenas o valor numérico positivo.
            4. DATA: Use o formato YYYY-MM-DD. Se não achar o ano, use 2026.

            RETORNO OBRIGATÓRIO:
            Retorne APENAS um JSON puro (sem markdown, sem ```json) no formato:
            [
                {"descricao": "Nome Limpo", "valor": 12.50, "categoria": "Categoria", "data": "2026-02-03"},
                ...
            ]
            """

            # Chamada para o modelo Gemini
            conteudo = [
                {"mime_type": mime_type, "data": arquivo_bytes},
                prompt
            ]

            response = self.model.generate_content(conteudo)

            # Limpeza rigorosa do texto para garantir que o json.loads não falhe
            json_text = response.text.strip()
            if "```" in json_text:
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:]

            return json.loads(json_text)

        except Exception as e:
            st.error(f"Erro no processamento da IA: {str(e)}")
            return []

    def gerar_insight(self, contexto: dict, mes_atual: str, indicadores: dict = None):
        """ Gera análise estratégica baseada em lançamentos e saldos. """
        if not self.model: return "IA indisponível."

        df_l = contexto.get("lancamentos", pd.DataFrame())
        df_l_limpo = df_l.drop(columns=[c for c in ['_id', 'id'] if c in df_l.columns]).tail(30)

        txt_indicadores = ""
        if indicadores:
            txt_indicadores = f"""
            - Saldo Real: R$ {indicadores.get('saldo_contas', 0):,.2f}
            - Saldo Livre Projetado: R$ {indicadores.get('saldo_projetado', 0):,.2f}
            """

        prompt = f"""
        Você é o Consultor do PlanejAI. Analise os dados:
        Mês: {mes_atual}
        {txt_indicadores}
        Lançamentos: {df_l_limpo.to_csv(index=False)}

        Dê 3 dicas curtas e encorajadoras sobre como economizar ou gerir o saldo este mês.
        """

        try:
            return self.model.generate_content(prompt).text
        except:
            return "Erro ao gerar análise."

    def chat(self, mensagem_usuario, contexto, indicadores: dict = None):
        if not self.model: return "IA indisponível."

        info = f"Saldo Projetado: R$ {indicadores.get('saldo_projetado', 0):,.2f}" if indicadores else ""
        prompt = f"Você é o assistente do PlanejAI. {info}. Responda: {mensagem_usuario}"

        try:
            return self.model.generate_content(prompt).text
        except:
            return "Desculpe, tive um problema ao processar isso."