import pandas as pd
from services.database_mongo import DatabaseMongo


class Database:
    """
    Fachada de persistência.
    Permite trocar Mongo / JSON / SQLite sem impactar o app.
    """

    @staticmethod
    def carregar_dados() -> pd.DataFrame:
        return DatabaseMongo.carregar_dados()

    @staticmethod
    def salvar_dados(df: pd.DataFrame):
        DatabaseMongo.salvar_dados(df)
