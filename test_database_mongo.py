from services.database_mongo import DatabaseMongo

db = DatabaseMongo()

db.inserir({
    "descricao": "Teste Mongo Classe",
    "valor": 500,
    "tipo": "receita",
    "categoria": "Teste",
    "mes_referencia": "2026-01",
    "fixo": False,
    "parcelado": False,
    "origem_id": None
})

print(db.listar_por_mes("2026-01"))
