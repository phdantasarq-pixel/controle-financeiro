import pandas as pd
import streamlit as st
from pymongo import MongoClient


class Database:
    @staticmethod
    def conectar():
        """Estabelece a conexão com o MongoDB LOCAL."""
        try:
            # URI padrão para o MongoDB rodando na sua máquina
            # Se você mudou a porta, troque 27017 pela sua
            uri = "mongodb://localhost:27017/"
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)  # 2 segundos de timeout

            # Testa a conexão
            client.admin.command('ping')

            return client["planejai"]
        except Exception as e:
            st.error(f"❌ Não consegui conectar ao MongoDB Local: {e}")
            st.info("Dica: Verifique se o serviço do MongoDB está iniciado (mongod).")
            return None

    @staticmethod
    def carregar_dados():
        """Carrega os lançamentos financeiros."""
        db = Database.conectar()
        if db is None:
            return pd.DataFrame()

        colecao = db["lancamentos"]
        dados = list(colecao.find())
        if not dados:
            return pd.DataFrame(
                columns=["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao"])

        df = pd.DataFrame(dados)
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
        return df

    @staticmethod
    def salvar_dados(df):
        """Salva os lançamentos financeiros (sobrescreve a coleção)."""
        db = Database.conectar()
        if db is not None:
            colecao = db["lancamentos"]
            colecao.delete_many({})
            if not df.empty:
                colecao.insert_many(df.to_dict("records"))

    # --- NOVOS MÉTODOS PARA SALDOS (H7.1) ---
    @staticmethod
    def carregar_saldos():
        """Carrega os saldos gerais das contas."""
        db = Database.conectar()
        if db is None:
            return pd.DataFrame(columns=["conta", "valor"])

        dados = list(db["saldos_gerais"].find({}, {"_id": 0}))
        return pd.DataFrame(dados) if dados else pd.DataFrame(columns=["conta", "valor"])

    @staticmethod
    def salvar_saldos(df_saldos):
        """Salva os saldos gerais (sobrescreve a coleção)."""
        db = Database.conectar()
        if db is not None:
            db["saldos_gerais"].delete_many({})
            if not df_saldos.empty:
                db["saldos_gerais"].insert_many(df_saldos.to_dict("records"))