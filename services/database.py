# services/database.py

import pandas as pd
from services.database_mongo import DatabaseMongo


class Database:
    """
    Fachada de persistência.
    O app inteiro usa esse Database, sem saber se é JSON ou Mongo.
    """

    @staticmethod
    def carregar_dados() -> pd.DataFrame:
        return DatabaseMongo.carregar_dados()

    @staticmethod
    def salvar_dados(df: pd.DataFrame):
        DatabaseMongo.salvar_dados(df)
