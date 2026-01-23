from dataclasses import dataclass
from datetime import date
from uuid import uuid4


@dataclass
class LancamentoFinanceiro:
    id: str
    descricao: str
    valor: float
    data: date
    tipo: str        # "receita" ou "despesa"
    pago: bool = False

    @staticmethod
    def novo(descricao, valor, data, tipo, pago=False):
        return LancamentoFinanceiro(
            id=str(uuid4()),
            descricao=descricao,
            valor=valor,
            data=data,
            tipo=tipo,
            pago=pago
        )
