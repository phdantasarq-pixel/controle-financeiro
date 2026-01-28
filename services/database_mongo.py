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

        if not docs:
            return pd.DataFrame(columns=DatabaseMongo.COLUNAS_PADRAO)

        for d in docs:
            d["_id"] = str(d["_id"])

        df = pd.DataFrame(docs)

        # Normaliza datas
        for col in ["data_vencimento", "data_registro"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    @staticmethod
    def salvar_dados(df: pd.DataFrame):
        if df.empty:
            DatabaseMongo._collection.delete_many({})
            return

        registros = df.copy()

        # Remove _id do pandas
        if "_id" in registros.columns:
            registros.drop(columns=["_id"], inplace=True)

        # 🔒 Blindagem TOTAL contra NaT
        for col in ["data_vencimento", "data_registro"]:
            if col not in registros.columns:
                registros[col] = datetime.now()
            else:
                registros[col] = pd.to_datetime(registros[col], errors="coerce")
                registros[col] = registros[col].fillna(pd.Timestamp.now())

        # Valor sempre float
        registros["valor"] = registros["valor"].astype(float).round(2)

        docs = registros.to_dict(orient="records")

        # Converte Timestamp → datetime nativo
        for d in docs:
            for campo in ["data_vencimento", "data_registro"]:
                if isinstance(d[campo], pd.Timestamp):
                    d[campo] = d[campo].to_pydatetime()

            d["created_at"] = datetime.utcnow()

        # Estratégia segura (igual JSON antigo)
        DatabaseMongo._collection.delete_many({})
        DatabaseMongo._collection.insert_many(docs)
