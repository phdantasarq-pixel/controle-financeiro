from dataclasses import dataclass
from datetime import date


@dataclass
class Receita:
    descricao: str
    valor: float
    recebido: bool
    data: date
