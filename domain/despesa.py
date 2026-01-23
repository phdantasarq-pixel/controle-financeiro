from dataclasses import dataclass
from datetime import date


@dataclass
class Despesa:
    descricao: str
    divida: bool
    paga: bool
    tipo: str          # "fixo" | "variavel"
    vencimento: date
    valor: float
