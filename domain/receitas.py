from dataclasses import dataclass

@dataclass
class Receita:
    pessoa: str
    pago: float
    deve: float
    descricao: str
