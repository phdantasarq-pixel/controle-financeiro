import google.generativeai as genai
import streamlit as st
import pandas as pd
import json
import os


class IAService:
    def __init__(self):
        # Tenta pegar dos secrets, se não existir, usa a chave fornecida
        self.api_key = st.secrets.get("GEMINI_API_KEY")
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
        Extrai dados de faturas, identifica o EMISSOR, a DATA DE VENCIMENTO e sanitiza os itens.
        """
        if not self.model:
            st.error("Modelo de IA não carregado.")
            return {"emissor": "Cartão", "vencimento": None, "itens": []}

        try:
            # Preparação dos dados do arquivo
            arquivo_bytes = arquivo.read()
            mime_type = arquivo.type

            # Reinicia o ponteiro do arquivo
            arquivo.seek(0)

            prompt = """
            Você é um especialista em análise de faturas do sistema PlanejAI.
            Analise o documento e extraia as informações seguindo estas regras:

            1. IDENTIFIQUE O EMISSOR: Nome do banco ou instituição (ex: Nubank, Inter, Itaú, Santander).
            2. DATA DE VENCIMENTO: Localize a data de vencimento da fatura (formato YYYY-MM-DD). Se não encontrar o ano, use 2026.
            3. SANITIZAÇÃO: Remova códigos e números de parcelas (ex: 'UBER *TRIP 123' -> 'Uber').
            4. CATEGORIZAÇÃO: Use EXATAMENTE uma destas: [Moradia, Alimentação, Transporte, Lazer, Saúde, Educação, Assinaturas, Cartão de Crédito, Outro].
            5. VALORES: Extraia apenas compras. Ignore pagamentos de fatura ou créditos.
            6. FORMATO NUMÉRICO: O valor deve ter apenas 2 casas decimais.

            RETORNO OBRIGATÓRIO (JSON PURO, SEM MARKDOWN):
            {
                "emissor": "Nome do Banco",
                "vencimento": "YYYY-MM-DD",
                "itens": [
                    {"descricao": "Nome Limpo", "valor": 12.50, "categoria": "Categoria", "data": "2026-02-03"},
                    ...
                ]
            }
            """

            # Chamada para o modelo Gemini
            conteudo = [
                {"mime_type": mime_type, "data": arquivo_bytes},
                prompt
            ]

            response = self.model.generate_content(conteudo)

            # Limpeza do texto para garantir JSON válido
            json_text = response.text.strip()
            if "```" in json_text:
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:]

            dados_extraidos = json.loads(json_text)

            # Garantia rigorosa de 2 casas decimais nos itens
            if "itens" in dados_extraidos:
                for item in dados_extraidos["itens"]:
                    item["valor"] = round(float(item["valor"]), 2)

            return dados_extraidos

        except Exception as e:
            st.error(f"Erro no processamento da IA: {str(e)}")
            return {"emissor": "Cartão", "vencimento": None, "itens": []}

    def gerar_insight(self, contexto: dict, mes_atual: str, indicadores: dict = None):
        """ Gera análise estratégica baseada em lançamentos e saldos. """
        if not self.model: return "IA indisponível."

        df_l = contexto.get("lancamentos", pd.DataFrame())
        # Remove campos internos para não confundir a IA
        colunas_remover = ['_id', 'id', 'detalhes']
        df_l_limpo = df_l.drop(columns=[c for c in colunas_remover if c in df_l.columns]).tail(30)

        txt_indicadores = ""
        if indicadores:
            txt_indicadores = f"""
            - Saldo Real: R$ {indicadores.get('saldo_contas', 0):,.2f}
            - Saldo Livre Projetado: R$ {indicadores.get('saldo_projetado', 0):,.2f}
            """

        prompt = f"""
        Você é o Consultor Estratégico do PlanejAI. Analise os dados financeiros abaixo:
        Mês de Referência: {mes_atual}
        {txt_indicadores}
        Últimos Lançamentos: 
        {df_l_limpo.to_csv(index=False)}

        Dê 3 dicas curtas, objetivas e encorajadoras sobre como economizar ou gerir o saldo este mês.
        """

        try:
            return self.model.generate_content(prompt).text
        except:
            return "Erro ao gerar análise financeira."

    def chat(self, mensagem_usuario, contexto, indicadores: dict = None):
        """ Responde dúvidas do usuário sobre o sistema ou finanças. """
        if not self.model: return "IA indisponível."

        info = f"Saldo Projetado: R$ {indicadores.get('saldo_projetado', 0):,.2f}" if indicadores else ""
        prompt = f"Você é o assistente inteligente do PlanejAI. {info}. Responda de forma clara: {mensagem_usuario}"

        try:
            return self.model.generate_content(prompt).text
        except:
            return "Desculpe, tive um problema ao processar sua pergunta agora."