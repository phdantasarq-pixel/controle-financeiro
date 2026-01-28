import pandas as pd
from pymongo import MongoClient
from datetime import datetime

class DatabaseMongo:
    """
    Implementação MongoDB compatível com a antiga Database (JSON).
    O app continua trabalhando com pandas DataFrame.
    """

    _client = MongoClient("mongodb://localhost:27017")
    _db = _client["planejai"]
    _collection = _db["lancamentos"]

    # Removido 'id' da lista para não poluir o DataFrame e a UI
    COLUNAS_PADRAO = [
        "data_vencimento",
        "data_registro",
        "tipo",
        "natureza",
        "valor",
        "categoria",
        "descricao"
    ]

    @staticmethod
    def carregar_dados() -> pd.DataFrame:
        docs = list(DatabaseMongo._collection.find())

        # Se vazio, devolve DataFrame com colunas padrão
        if not docs:
            return pd.DataFrame(columns=DatabaseMongo.COLUNAS_PADRAO)

        # Remove o _id do MongoDB para que o Pandas não o transforme em coluna
        for d in docs:
            if "_id" in d:
                del d["_id"]

        df = pd.DataFrame(docs)

        # Garante colunas mesmo se algum documento estiver faltando
        for col in DatabaseMongo.COLUNAS_PADRAO:
            if col not in df.columns:
                df[col] = None

        # Normaliza datas
        df["data_vencimento"] = pd.to_datetime(df["data_vencimento"], errors="coerce")
        df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")

        # Normaliza valor
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)

        # Reordena para manter o contrato limpo
        return df[DatabaseMongo.COLUNAS_PADRAO]

    @staticmethod
    def salvar_dados(df: pd.DataFrame):
        """
        Estratégia: delete tudo e insere de novo.
        O MongoDB gera novos _id automaticamente a cada salvamento.
        """
        DatabaseMongo._collection.delete_many({})

        if df.empty:
            return

        registros = df.copy()

        # Garante que campos de ID residuais não sejam enviados
        for col in ["id", "_id"]:
            if col in registros.columns:
                registros = registros.drop(columns=[col])

        # Normaliza datas para datetime nativo do Python (essencial para o Mongo)
        registros["data_vencimento"] = pd.to_datetime(
            registros["data_vencimento"], errors="coerce"
        ).dt.to_pydatetime()
        registros["data_registro"] = pd.to_datetime(
            registros["data_registro"], errors="coerce"
        ).dt.to_pydatetime()

        registros["valor"] = registros["valor"].astype(float).round(2)

        docs = registros.to_dict(orient="records")

        # Adiciona timestamp de criação
        for d in docs:
            d["created_at"] = datetime.utcnow()

        DatabaseMongo._collection.insert_many(docs)